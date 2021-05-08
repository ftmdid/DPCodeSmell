import markdown
import logging
import traceback
import urllib.parse
import re
import os.path
import glob
import twitter
import platform
import time
import html.parser
import httplib2

import hashlib
import hmac

from django.core import mail
from django.conf import settings

from zerver.lib.avatar  import gravatar_hash
from zerver.lib.bugdown import codehilite, fenced_code
from zerver.lib.bugdown.fenced_code import FENCE_RE
from zerver.lib.timeout import timeout, TimeoutExpired
from zerver.lib.cache import cache_with_key, cache_get_many, cache_set_many
import zerver.lib.alert_words as alert_words
import zerver.lib.mention as mention


if settings.USING_EMBEDLY:
    from embedly import Embedly
    embedly_client = Embedly(settings.EMBEDLY_KEY, timeout=2.5)

# Format version of the bugdown rendering; stored along with rendered
# messages so that we can efficiently determine what needs to be re-rendered
version = 1

def list_of_tlds():
    # HACK we manually blacklist .py
    blacklist = ['PY\n', ]

    # tlds-alpha-by-domain.txt comes from http://data.iana.org/TLD/tlds-alpha-by-domain.txt
    tlds_file = os.path.join(os.path.dirname(__file__), 'tlds-alpha-by-domain.txt')
    tlds = [tld.lower().strip() for tld in open(tlds_file, 'r')
                if not tld in blacklist and not tld[0].startswith('#')]
    tlds.sort(key=len, reverse=True)
    return tlds

def walk_tree(root, processor, stop_after_first=False):
    results = []
    stack = [root]

    while stack:
        currElement = stack.pop()
        for child in currElement.getchildren():
            if child.getchildren():
                stack.append(child)

            result = processor(child)
            if result is not None:
                results.append(result)
                if stop_after_first:
                    return results

    return results

def add_a(root, url, link, height=None):
    div = markdown.util.etree.SubElement(root, "div")
    div.set("class", "message_inline_image");
    a = markdown.util.etree.SubElement(div, "a")
    a.set("href", link)
    a.set("target", "_blank")
    a.set("title", link)
    img = markdown.util.etree.SubElement(a, "img")
    img.set("src", url)

def hash_embedly_url(link):
    return 'embedly:' + hashlib.sha1(link).hexdigest()

@cache_with_key(lambda tweet_id: tweet_id, cache_name="database", with_statsd_key="tweet_data")
def fetch_tweet_data(tweet_id):
    if settings.TEST_SUITE:
        import testing_mocks
        res = testing_mocks.twitter(tweet_id)
    else:
        api = twitter.Api(consumer_key = settings.TWITTER_CONSUMER_KEY,
                          consumer_secret = settings.TWITTER_CONSUMER_SECRET,
                          access_token_key = settings.TWITTER_ACCESS_TOKEN_KEY,
                          access_token_secret = settings.TWITTER_ACCESS_TOKEN_SECRET)

        try:
            # Sometimes Twitter hangs on responses.  Timing out here
            # will cause the Tweet to go through as-is with no inline
            # preview, rather than having the message be rejected
            # entirely. This timeout needs to be less than our overall
            # formatting timeout.
            res = timeout(3, api.GetStatus, tweet_id).AsDict()
        except TimeoutExpired as e:
            # We'd like to try again later and not cache the bad result,
            # so we need to re-raise the exception (just as though
            # we were being rate-limited)
            raise
        except twitter.TwitterError as e:
            t = e.args[0]
            if len(t) == 1 and ('code' in t[0]) and (t[0]['code'] == 34):
                # Code 34 means that the message doesn't exist; return
                # None so that we will cache the error
                return None
            elif len(t) == 1 and ('code' in t[0]) and (t[0]['code'] == 88 or
                                                       t[0]['code'] == 130):
                # Code 88 means that we were rate-limited and 130
                # means Twitter is having capacity issues; either way
                # just raise the error so we don't cache None and will
                # try again later.
                raise
            else:
                # It's not clear what to do in cases of other errors,
                # but for now it seems reasonable to log at error
                # level (so that we get notified), but then cache the
                # failure to proceed with our usual work
                logging.error(traceback.format_exc())
                return None
    return res

def get_tweet_id(url):
    parsed_url = urllib.parse.urlparse(url)
    if not (parsed_url.netloc == 'twitter.com' or parsed_url.netloc.endswith('.twitter.com')):
        return False

    tweet_id_match = re.match(r'^/.*?/status(es)?/(?P<tweetid>\d{18})$', parsed_url.path)
    if not tweet_id_match:
        return False
    return tweet_id_match.group("tweetid")

class InlineHttpsProcessor(markdown.treeprocessors.Treeprocessor):
    def run(self, root):
        # Get all URLs from the blob
        found_imgs = walk_tree(root, lambda e: e if e.tag == "img" else None)
        for img in found_imgs:
            url = img.get("src")
            # We rewrite all HTTP URLs as well as all HTTPs URLs for mit.edu
            if not (url.startswith("http://") or
                    (url.startswith("https://") and
                     current_message is not None and
                     current_message.sender.realm.domain == "mit.edu")):
                # Don't rewrite images on our own site (e.g. emoji).
                continue
            digest = hmac.new(settings.CAMO_KEY, url, hashlib.sha1).hexdigest()
            encoded_url = url.encode("hex")
            img.set("src", "https://external-content.zulipcdn.net/%s/%s" % (digest, encoded_url))

class InlineInterestingLinkProcessor(markdown.treeprocessors.Treeprocessor):
    def is_image(self, url):
        parsed_url = urllib.parse.urlparse(url)
        # List from http://support.google.com/chromeos/bin/answer.py?hl=en&answer=183093
        for ext in [".bmp", ".gif", ".jpg", "jpeg", ".png", ".webp"]:
            if parsed_url.path.lower().endswith(ext):
                return True
        return False

    def dropbox_image(self, url):
        if not self.is_image(url):
            return None
        parsed_url = urllib.parse.urlparse(url)
        if (parsed_url.netloc == 'dropbox.com' or parsed_url.netloc.endswith('.dropbox.com')) \
                and (parsed_url.path.startswith('/s/') or parsed_url.path.startswith('/sh/')):
            return "%s?dl=1" % (url,)
        return None

    def youtube_image(self, url):
        # Youtube video id extraction regular expression from http://pastebin.com/KyKAFv1s
        # If it matches, match.group(2) is the video id.
        youtube_re = r'^((?:https?://)?(?:youtu\.be/|(?:\w+\.)?youtube(?:-nocookie)?\.com/)(?:(?:(?:v|embed)/)|(?:(?:watch(?:_popup)?(?:\.php)?)?(?:\?|#!?)(?:.+&)?v=)))?([0-9A-Za-z_-]+)(?(1).+)?$'
        match = re.match(youtube_re, url)
        if match is None:
            return None
        return "https://i.ytimg.com/vi/%s/default.jpg" % (match.group(2),)

    def twitter_link(self, url):
        tweet_id = get_tweet_id(url)

        if not tweet_id:
            return None

        try:
            res = fetch_tweet_data(tweet_id)
            if res is None:
                return None
            user = res['user']
            tweet = markdown.util.etree.Element("div")
            tweet.set("class", "twitter-tweet")
            img_a = markdown.util.etree.SubElement(tweet, 'a')
            img_a.set("href", url)
            img_a.set("target", "_blank")
            profile_img = markdown.util.etree.SubElement(img_a, 'img')
            profile_img.set('class', 'twitter-avatar')
            # For some reason, for, e.g. tweet 285072525413724161,
            # python-twitter does not give us a
            # profile_image_url_https, but instead puts that URL in
            # profile_image_url. So use _https if available, but fall
            # back gracefully.
            image_url = user.get('profile_image_url_https', user['profile_image_url'])
            profile_img.set('src', image_url)
            p = markdown.util.etree.SubElement(tweet, 'p')
            ## TODO: unescape is an internal function, so we should
            ## use something else if we can find it
            p.text = html.parser.HTMLParser().unescape(res['text'])
            span = markdown.util.etree.SubElement(tweet, 'span')
            span.text = "- %s (@%s)" % (user['name'], user['screen_name'])

            return tweet
        except:
            # We put this in its own try-except because it requires external
            # connectivity. If Twitter flakes out, we don't want to not-render
            # the entire message; we just want to not show the Twitter preview.
            logging.warning(traceback.format_exc())
            return None

    def do_embedly(self, root, supported_urls):
        # embed.ly support is disabled until it can be
        # properly debugged.
        #
        # We're not deleting the code for now, since we expect to
        # restore it and want to be able to update it along with
        # future refactorings rather than keeping it as a separate
        # branch.
        if not settings.USING_EMBEDLY:
            return

        # We want this to be able to easily reverse the hashing later
        keys_to_links = dict((hash_embedly_url(link), link) for link in supported_urls)
        cache_hits = cache_get_many(list(keys_to_links.keys()), cache_name="database")

        # Construct a dict of url => oembed_data pairs
        oembeds = dict((keys_to_links[key], cache_hits[key]) for key in cache_hits)

        to_process = [url for url in supported_urls if not url in oembeds]
        to_cache = {}

        if to_process:
            # Don't touch embed.ly if we have everything cached.
            try:
                responses = embedly_client.oembed(to_process, maxwidth=250)
            except httplib2.socket.timeout:
                # We put this in its own try-except because it requires external
                # connectivity. If embedly flakes out, we don't want to not-render
                # the entire message; we just want to not show the embedly preview.
                logging.warning("Embedly Embed timeout for URLs: %s" % (" ".join(to_process)))
                logging.warning(traceback.format_exc())
                return root
            except Exception:
                # If things break for any other reason, don't make things sad.
                logging.warning(traceback.format_exc())
                return root
            for oembed_data in responses:
                # Don't cache permanent errors
                if oembed_data["type"] == "error" and \
                        oembed_data["error_code"] in (500, 501, 503):
                    continue
                # Convert to dict because otherwise pickling won't work.
                to_cache[oembed_data["original_url"]] = dict(oembed_data)

            # Cache the newly collected data to the database
            cache_set_many(dict((hash_embedly_url(link), to_cache[link]) for link in to_cache),
                           cache_name="database")
            oembeds.update(to_cache)

        # Now let's process the URLs in order
        for link in supported_urls:
            oembed_data = oembeds[link]

            if oembed_data["type"] in ("link"):
                continue
            elif oembed_data["type"] in ("video", "rich") and "script" not in oembed_data["html"]:
                placeholder = self.markdown.htmlStash.store(oembed_data["html"], safe=True)
                el = markdown.util.etree.SubElement(root, "p")
                el.text = placeholder
            else:
                try:
                    add_a(root,
                          oembed_data["thumbnail_url"],
                          link,
                          height=oembed_data["thumbnail_height"])
                except KeyError:
                    # We didn't have a thumbnail, so let's just bail and keep on going...
                    continue
        return root

    def run(self, root):
        # Get all URLs from the blob
        found_urls = walk_tree(root, lambda e: e.get("href") if e.tag == "a" else None)

        # If there are more than 5 URLs in the message, don't do inline previews
        if len(found_urls) == 0 or len(found_urls) > 5:
            return

        rendered_tweet = False
        embedly_urls = []
        for url in found_urls:
            dropbox = self.dropbox_image(url)
            if dropbox is not None:
                add_a(root, dropbox, url)
                continue
            if self.is_image(url):
                add_a(root, url, url)
                continue
            if get_tweet_id(url):
                if rendered_tweet:
                    # Only render at most one tweet per message
                    continue
                twitter_data = self.twitter_link(url)
                if twitter_data is None:
                    # This link is not actually a tweet known to twitter
                    continue
                rendered_tweet = True
                div = markdown.util.etree.SubElement(root, "div")
                div.set("class", "inline-preview-twitter")
                div.insert(0, twitter_data)
                continue
            if settings.USING_EMBEDLY:
                if embedly_client.is_supported(url):
                    embedly_urls.append(url)
                    continue
            # NOTE: The youtube code below is inactive at least on
            # staging because embedy.ly is currently handling those
            youtube = self.youtube_image(url)
            if youtube is not None:
                add_a(root, youtube, url)
                continue

        if settings.USING_EMBEDLY:
            self.do_embedly(root, embedly_urls)

class Gravatar(markdown.inlinepatterns.Pattern):
    def handleMatch(self, match):
        img = markdown.util.etree.Element('img')
        img.set('class', 'message_body_gravatar img-rounded')
        img.set('src', 'https://secure.gravatar.com/avatar/%s?d=identicon&s=30'
            % (gravatar_hash(match.group('email')),))
        return img

path_to_emoji = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                             # This should be the root
                             'static', 'third', 'gemoji', 'images', 'emoji', '*.png')
emoji_list = [os.path.splitext(os.path.basename(fn))[0] for fn in glob.glob(path_to_emoji)]

def make_emoji(emoji_name, src, display_string):
    elt = markdown.util.etree.Element('img')
    elt.set('src', src)
    elt.set('class', 'emoji')
    elt.set("alt", display_string)
    elt.set("title", display_string)
    return elt

class Emoji(markdown.inlinepatterns.Pattern):
    def handleMatch(self, match):
        orig_syntax = match.group("syntax")
        name = orig_syntax[1:-1]

        realm_emoji = {}
        if db_data is not None:
            realm_emoji = db_data['emoji']

        if current_message and name in realm_emoji:
            return make_emoji(name, realm_emoji[name], orig_syntax)
        elif name in emoji_list:
            src = 'static/third/gemoji/images/emoji/%s.png' % (name)
            return make_emoji(name, src, orig_syntax)
        else:
            return None

def fixup_link(link, target_blank=True):
    """Set certain attributes we want on every link."""
    if target_blank:
        link.set('target', '_blank')
    link.set('title',  link.get('href'))


def sanitize_url(url):
    """
    Sanitize a url against xss attacks.
    See the docstring on markdown.inlinepatterns.LinkPattern.sanitize_url.
    """
    try:
        parts = urllib.parse.urlparse(url.replace(' ', '%20'))
        scheme, netloc, path, params, query, fragment = parts
    except ValueError:
        # Bad url - so bad it couldn't be parsed.
        return ''

    # If there is no scheme or netloc and there is a '@' in the path,
    # treat it as a mailto: and set the appropriate scheme
    if scheme == '' and netloc == '' and '@' in path:
        scheme = 'mailto'

    # Zulip modification: If scheme is not specified, assume http://
    # It's unlikely that users want relative links within zulip.com.
    # We re-enter sanitize_url because netloc etc. need to be re-parsed.
    if not scheme:
        return sanitize_url('http://' + url)

    locless_schemes = ['mailto', 'news']
    if netloc == '' and scheme not in locless_schemes:
        # This fails regardless of anything else.
        # Return immediately to save additional proccessing
        return None

    # Upstream code will accept a URL like javascript://foo because it
    # appears to have a netloc.  Additionally there are plenty of other
    # schemes that do weird things like launch external programs.  To be
    # on the safe side, we whitelist the scheme.
    if scheme not in ('http', 'https', 'ftp', 'mailto'):
        return None

    # Upstream code scans path, parameters, and query for colon characters
    # because
    #
    #    some aliases [for javascript:] will appear to urlparse() to have
    #    no scheme. On top of that relative links (i.e.: "foo/bar.html")
    #    have no scheme.
    #
    # We already converted an empty scheme to http:// above, so we skip
    # the colon check, which would also forbid a lot of legitimate URLs.

    # Url passes all tests. Return url as-is.
    return urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))

def url_to_a(url, text = None):
    a = markdown.util.etree.Element('a')

    href = sanitize_url(url)
    if href is None:
        # Rejected by sanitize_url; render it as plain text.
        return url
    if text is None:
        text = markdown.util.AtomicString(url)

    a.set('href', href)
    a.text = text
    fixup_link(a, not 'mailto:' in href[:7])
    return a

class AutoLink(markdown.inlinepatterns.Pattern):
    def __init__(self, pattern):
        markdown.inlinepatterns.Pattern.__init__(self, ' ')

        # HACK: we just had python-markdown compile an empty regex.
        # Now replace with the real regex compiled with the flags we want.

        self.pattern = pattern
        self.compiled_re = re.compile("^(.*?)%s(.*?)$" % pattern,
                                      re.DOTALL | re.UNICODE | re.VERBOSE)

    def handleMatch(self, match):
        url = match.group('url')
        return url_to_a(url)

class UListProcessor(markdown.blockprocessors.OListProcessor):
    """ Process unordered list blocks.

        Based on markdown.blockprocessors.UListProcessor, but does not accept
        '+' or '-' as a bullet character."""

    TAG = 'ul'
    RE = re.compile(r'^[ ]{0,3}[*][ ]+(.*)')

class BugdownUListPreprocessor(markdown.preprocessors.Preprocessor):
    """ Allows unordered list blocks that come directly after a
        paragraph to be rendered as an unordered list

        Detects paragraphs that have a matching list item that comes
        directly after a line of text, and inserts a newline between
        to satisfy Markdown"""

    LI_RE = re.compile(r'^[ ]{0,3}[*][ ]+(.*)', re.MULTILINE)
    HANGING_ULIST_RE = re.compile(r'^.+\n([ ]{0,3}[*][ ]+.*)', re.MULTILINE)

    def run(self, lines):
        """ Insert a newline between a paragraph and ulist if missing """
        inserts = 0
        fence = None
        copy = lines[:]
        for i in range(len(lines) - 1):
            # Ignore anything that is inside a fenced code block
            m = FENCE_RE.match(lines[i])
            if not fence and m:
                fence = m.group('fence')
            elif fence and m and fence == m.group('fence'):
                fence = None

            # If we're not in a fenced block and we detect an upcoming list
            #  hanging off a paragraph, add a newline
            if not fence and lines[i] and \
                self.LI_RE.match(lines[i+1]) and not self.LI_RE.match(lines[i]):
                copy.insert(i+inserts+1, '')
                inserts += 1
        return copy

# Based on markdown.inlinepatterns.LinkPattern
class LinkPattern(markdown.inlinepatterns.Pattern):
    """ Return a link element from the given match. """
    def handleMatch(self, m):
        href = m.group(9)
        if not href:
            return None

        if href[0] == "<":
            href = href[1:-1]
        href = sanitize_url(self.unescape(href.strip()))
        if href is None:
            return None

        el = markdown.util.etree.Element('a')
        el.text = m.group(2)
        el.set('href', href)
        fixup_link(el)
        return el

def prepare_realm_pattern(source):
    """ Augment a realm filter so it only matches after start-of-string,
    whitespace, or opening delimiters, won't match if there are word
    characters directly after, and saves what was matched as "name". """
    return r"""(?<![^\s'"\(,:<])(?P<name>""" + source + ')(?!\w)'

# Given a regular expression pattern, linkifies groups that match it
# using the provided format string to construct the URL.
class RealmFilterPattern(markdown.inlinepatterns.Pattern):
    """ Applied a given realm filter to the input """
    def __init__(self, source_pattern, format_string, markdown_instance=None):
        self.pattern = prepare_realm_pattern(source_pattern)
        self.format_string = format_string
        markdown.inlinepatterns.Pattern.__init__(self, self.pattern, markdown_instance)

    def handleMatch(self, m):
        return url_to_a(self.format_string % m.groupdict(),
                        m.group("name"))

class UserMentionPattern(markdown.inlinepatterns.Pattern):
    def find_user_for_mention(self, name):
        if db_data is None:
            return (False, None)

        if mention.user_mention_matches_wildcard(name):
            return (True, None)

        user = db_data['full_names'].get(name.lower(), None)
        if user is None:
            user = db_data['short_names'].get(name.lower(), None)

        return (False, user)

    def handleMatch(self, m):
        name = m.group(2) or m.group(3)

        if current_message:
            wildcard, user = self.find_user_for_mention(name)

            if wildcard:
                current_message.mentions_wildcard = True
                email = "*"
            elif user:
                current_message.mentions_user_ids.add(user['id'])
                name = user['full_name']
                email = user['email']
            else:
                # Don't highlight @mentions that don't refer to a valid user
                return None

            el = markdown.util.etree.Element("span")
            el.set('class', 'user-mention')
            el.set('data-user-email', email)
            el.text = "@%s" % (name,)
            return el

class AlertWordsNotificationProcessor(markdown.preprocessors.Preprocessor):
    def run(self, lines):
        if current_message and db_data is not None:
            # We check for a user's custom notifications here, as we want
            # to check for plaintext words that depend on the recipient.
            realm_words = db_data['realm_alert_words']
            content = '\n'.join(lines).lower()

            allowed_before_punctuation = "|".join([r'\s', '^', r'[\(\"]'])
            allowed_after_punctuation = "|".join([r'\s', '$', r'[\)\"\?:.,]'])

            for user_id, words in list(realm_words.items()):
                for word in words:
                    escaped = re.escape(word.lower())
                    match_re = re.compile(r'(?:%s)%s(?:%s)' %
                                            (allowed_before_punctuation,
                                             escaped,
                                             allowed_after_punctuation))
                    if re.search(match_re, content):
                        current_message.user_ids_with_alert_words.add(user_id)

        return lines

# This prevents realm_filters from running on the content of a
# Markdown link, breaking up the link.  This is a monkey-patch, but it
# might be worth sending a version of this change upstream.
class AtomicLinkPattern(LinkPattern):
    def handleMatch(self, m):
        ret = LinkPattern.handleMatch(self, m)
        if ret is None:
            return None
        if not isinstance(ret, str):
            ret.text = markdown.util.AtomicString(ret.text)
        return ret

class Bugdown(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        del md.preprocessors['reference']

        for k in ('image_link', 'image_reference', 'automail',
                  'autolink', 'link', 'reference', 'short_reference',
                  'escape', 'strong_em', 'emphasis', 'emphasis2',
                  'strong'):
            del md.inlinePatterns[k]

        md.preprocessors.add("custom_text_notifications", AlertWordsNotificationProcessor(md), "_end")

        # Custom bold syntax: **foo** but not __foo__
        md.inlinePatterns.add('strong',
            markdown.inlinepatterns.SimpleTagPattern(r'(\*\*)([^\n]+?)\2', 'strong'),
            '>not_strong')

        for k in ('hashheader', 'setextheader', 'olist', 'ulist'):
            del md.parser.blockprocessors[k]

        md.parser.blockprocessors.add('ulist', UListProcessor(md.parser), '>hr')

        md.inlinePatterns.add('gravatar', Gravatar(r'!gravatar\((?P<email>[^)]*)\)'), '_begin')
        md.inlinePatterns.add('usermention', UserMentionPattern(mention.find_mentions), '>backtick')
        md.inlinePatterns.add('emoji', Emoji(r'(?<!\w)(?P<syntax>:[^:\s]+:)(?!\w)'), '_end')
        md.inlinePatterns.add('link', AtomicLinkPattern(markdown.inlinepatterns.LINK_RE, md), '>backtick')

        for (pattern, format_string) in self.getConfig("realm_filters"):
            md.inlinePatterns.add('realm_filters/%s' % (pattern,),
                                  RealmFilterPattern(pattern, format_string), '>link')

        # A link starts at a word boundary, and ends at space, punctuation, or end-of-input.
        #
        # We detect a url either by the `https?://` or by building around the TLD.
        tlds = '|'.join(list_of_tlds())
        link_regex = r"""
            (?<![^\s'"\(,:<])    # Start after whitespace or specified chars
                                 # (Double-negative lookbehind to allow start-of-string)
            (?P<url>             # Main group
                (?:(?:           # Domain part
                    https?://[\w.:@-]+?   # If it has a protocol, anything goes.
                   |(?:                   # Or, if not, be more strict to avoid false-positives
                        (?:[\w-]+\.)+     # One or more domain components, separated by dots
                        (?:%s)            # TLDs (filled in via format from tlds-alpha-by-domain.txt)
                    )
                )
                (?:/             # A path, beginning with /
                    [^\s()\"]*?            # Containing characters that won't end the URL
                    (?: \( [^\s()\"]* \)   # and more characters in matched parens
                        [^\s()\"]*?        # followed by more characters
                    )*                     # zero-or-more sets of paired parens
                )?)              # Path is optional
                | (?:[\w.-]+\@[\w.-]+\.[\w]+) # Email is separate, since it can't have a path
            )
            (?=                            # URL must be followed by (not included in group)
                [:;\?\),\.\'\"\>]*         # Optional punctuation characters
                (?:\Z|\s)                  # followed by whitespace or end of string
            )
            """ % (tlds,)
        md.inlinePatterns.add('autolink', AutoLink(link_regex), '>link')

        md.preprocessors.add('hanging_ulists',
                                 BugdownUListPreprocessor(md),
                                 "_begin")

        md.treeprocessors.add("inline_interesting_links", InlineInterestingLinkProcessor(md), "_end")
        md.treeprocessors.add("rewrite_to_https", InlineHttpsProcessor(md), "_end")

        if self.getConfig("realm") == "mit.edu/zephyr_mirror":
            # Disable almost all inline patterns for mit.edu users' traffic that is mirrored
            # Note that inline_interesting_links is a treeprocessor and thus is not removed
            for k in list(md.inlinePatterns.keys()):
                if k not in ["autolink"]:
                    del md.inlinePatterns[k]


md_engines = {}

def make_md_engine(key, opts):
    md_engines[key] = markdown.Markdown(
        safe_mode     = 'escape',
        output_format = 'html',
        extensions    = ['nl2br',
                         codehilite.makeExtension(configs=[
                    ('force_linenos', False),
                    ('guess_lang',    False)]),
                         fenced_code.makeExtension(),
                         Bugdown(opts)])

realm_filters = {
    "default": [],
    "zulip.com": [
        ("#(?P<id>[0-9]{2,8})", "https://trac.zulip.net/ticket/%(id)s"),
        ],
    "mit.edu/zephyr_mirror": [],
    }

def subject_links(domain, subject):
    matches = []
    for source_pattern, format_string in realm_filters.get(domain, []):
        pattern = prepare_realm_pattern(source_pattern)
        for m in re.finditer(pattern, subject):
            matches += [format_string % m.groupdict()]
    return matches

for realm in list(realm_filters.keys()):
    # Because of how the Markdown config API works, this has confusing
    # large number of layers of dicts/arrays :(
    make_md_engine(realm, {"realm_filters": [realm_filters[realm], "Realm-specific filters for %s" % (realm,)],
                           "realm": [realm, "Realm name"]})

# We want to log Markdown parser failures, but shouldn't log the actual input
# message for privacy reasons.  The compromise is to replace all alphanumeric
# characters with 'x'.
#
# We also use repr() to improve reproducibility, and to escape terminal control
# codes, which can do surprisingly nasty things.
_privacy_re = re.compile(r'\w', flags=re.UNICODE)
def _sanitize_for_log(md):
    return repr(_privacy_re.sub('x', md))


# Filters such as UserMentionPattern need a message, but python-markdown
# provides no way to pass extra params through to a pattern. Thus, a global.
current_message = None

# We avoid doing DB queries in our markdown thread to avoid the overhead of
# opening a new DB connection. These connections tend to live longer than the
# threads themselves, as well.
db_data = None

def do_convert(md, realm_domain=None, message=None):
    """Convert Markdown to HTML, with Zulip-specific settings and hacks."""
    from zerver.models import UserProfile

    if realm_domain in md_engines:
        _md_engine = md_engines[realm_domain]
    else:
        _md_engine = md_engines["default"]
    # Reset the parser; otherwise it will get slower over time.
    _md_engine.reset()

    global current_message
    current_message = message

    # Pre-fetch data from the DB that is used in the bugdown thread
    global db_data
    if message:
        realm_users = UserProfile.objects.filter(realm=message.get_realm(), is_active=True) \
                                         .values('id', 'full_name', 'short_name', 'email')

        db_data = {'realm_alert_words': alert_words.alert_words_in_realm(message.get_realm()),
                   'full_names':        dict((user['full_name'].lower(), user) for user in realm_users),
                   'short_names':       dict((user['short_name'].lower(), user) for user in realm_users),
                   'emoji':             message.get_realm().get_emoji()}

    try:
        # Spend at most 5 seconds rendering.
        # Sometimes Python-Markdown is really slow; see
        # https://trac.zulip.net/ticket/345
        return timeout(5, _md_engine.convert, md)
    except:
        from zerver.lib.actions import internal_send_message

        cleaned = _sanitize_for_log(md)

        # Output error to log as well as sending a zulip and email
        logging.getLogger('').error('Exception in Markdown parser: %sInput (sanitized) was: %s'
            % (traceback.format_exc(), cleaned))
        subject = "Markdown parser failure on %s" % (platform.node(),)
        internal_send_message("error-bot@zulip.com", "stream",
                "errors", subject, "Markdown parser failed, email sent with details.")
        mail.mail_admins(subject, "Failed message: %s\n\n%s\n\n" % (
                                    cleaned, traceback.format_exc()),
                         fail_silently=False)
        return None
    finally:
        current_message = None
        db_data = None

bugdown_time_start = 0
bugdown_total_time = 0
bugdown_total_requests = 0

def get_bugdown_time():
    return bugdown_total_time

def get_bugdown_requests():
    return bugdown_total_requests

def bugdown_stats_start():
    global bugdown_time_start
    bugdown_time_start = time.time()

def bugdown_stats_finish():
    global bugdown_total_time
    global bugdown_total_requests
    global bugdown_time_start
    bugdown_total_requests += 1
    bugdown_total_time += (time.time() - bugdown_time_start)

def convert(md, realm_domain=None, message=None):
    bugdown_stats_start()
    ret = do_convert(md, realm_domain, message)
    bugdown_stats_finish()
    return ret