"""
unixccompiler - can handle very long argument lists for ar.
"""

import os
import sys
import new

from distutils.errors import DistutilsExecError, LinkError, CompileError
from distutils.unixccompiler import *


import log

# Note that UnixCCompiler._compile appeared in Python 2.3
def UnixCCompiler__compile(self, obj, src, ext, cc_args, extra_postargs, pp_opts):
    display = '%s: %s' % (os.path.basename(self.compiler_so[0]),src)
    try:
        self.spawn(self.compiler_so + cc_args + [src, '-o', obj] +
                   extra_postargs, display = display)
    except DistutilsExecError, msg:
        raise CompileError, msg
UnixCCompiler._compile = new.instancemethod(UnixCCompiler__compile,
                                            None,
                                            UnixCCompiler)


def UnixCCompile_create_static_lib(self, objects, output_libname,
                                   output_dir=None, debug=0, target_lang=None):
    objects, output_dir = self._fix_object_args(objects, output_dir)

    output_filename = \
                    self.library_filename(output_libname, output_dir=output_dir)

    if self._need_link(objects, output_filename):
        self.mkpath(os.path.dirname(output_filename))
        tmp_objects = objects + self.objects
        while tmp_objects:
            objects = tmp_objects[:50]
            tmp_objects = tmp_objects[50:]
            display = '%s: adding %d object files to %s' % (os.path.basename(self.archiver[0]),
                                               len(objects),output_filename)
            self.spawn(self.archiver + [output_filename] + objects,
                       display = display)

        # Not many Unices required ranlib anymore -- SunOS 4.x is, I
        # think the only major Unix that does.  Maybe we need some
        # platform intelligence here to skip ranlib if it's not
        # needed -- or maybe Python's configure script took care of
        # it for us, hence the check for leading colon.
        if self.ranlib:
            display = '%s:@ %s' % (os.path.basename(self.ranlib[0]),
                                   output_filename)
            try:
                self.spawn(self.ranlib + [output_filename],
                           display = display)
            except DistutilsExecError, msg:
                raise LibError, msg
    else:
        log.debug("skipping %s (up-to-date)", output_filename)
    return

UnixCCompiler.create_static_lib = \
  new.instancemethod(UnixCCompile_create_static_lib,
                     None,UnixCCompiler)

#!/usr/bin/python

# takes templated file .xxx.src and produces .xxx file  where .xxx is .i or .c or .h
#  using the following template rules

# /**begin repeat     on a line by itself marks the beginning of a segment of code to be repeated
# /**end repeat**/    on a line by itself marks it's end

# after the /**begin repeat and before the */
#  all the named templates are placed
#  these should all have the same number of replacements

#  in the main body, the names are used.
#  Each replace will use one entry from the list of named replacements

#  Note that all #..# forms in a block must have the same number of
#    comma-separated entries.

__all__ = ['process_str', 'process_file']

import os
import sys
import re

def parse_structure(astr):
    spanlist = []
    # subroutines
    ind = 0
    line = 1
    while 1:
        start = astr.find("/**begin repeat", ind)
        if start == -1:
            break
        start2 = astr.find("*/",start)
        start2 = astr.find("\n",start2)
        fini1 = astr.find("/**end repeat**/",start2)
        fini2 = astr.find("\n",fini1)
        line += astr.count("\n", ind, start2+1)
        spanlist.append((start, start2+1, fini1, fini2+1, line))
        line += astr.count("\n", start2+1, fini2)
        ind = fini2
    spanlist.sort()
    return spanlist

# return n copies of substr with template replacement
_special_names = {}

template_re = re.compile(r"@([\w]+)@")
named_re = re.compile(r"#([\w]*)=([^#]*?)#")

parenrep = re.compile(r"[(]([^)]*?)[)]\*(\d+)")
def paren_repl(obj):
    torep = obj.group(1)
    numrep = obj.group(2)
    return ','.join([torep]*int(numrep))

plainrep = re.compile(r"([^*]+)\*(\d+)")

def conv(astr):
    # replaces all occurrences of '(a,b,c)*4' in astr
    #  with 'a,b,c,a,b,c,a,b,c,a,b,c'
    astr = parenrep.sub(paren_repl,astr)
    # replaces occurences of xxx*3 with xxx, xxx, xxx
    astr = ','.join([plainrep.sub(paren_repl,x.strip())
                     for x in astr.split(',')])
    return astr

def unique_key(adict):
    # this obtains a unique key given a dictionary
    # currently it works by appending together n of the letters of the
    #   current keys and increasing n until a unique key is found
    # -- not particularly quick
    allkeys = adict.keys()
    done = False
    n = 1
    while not done:
        newkey = "".join([x[:n] for x in allkeys])
        if newkey in allkeys:
            n += 1
        else:
            done = True
    return newkey

def expand_sub(substr, namestr, line):
    # find all named replacements
    reps = named_re.findall(namestr)
    names = {}
    names.update(_special_names)
    numsubs = None
    for rep in reps:
        name = rep[0].strip()
        thelist = conv(rep[1])
        names[name] = thelist

    # make lists out of string entries in name dictionary
    for name in names.keys():
        entry = names[name]
        entrylist = entry.split(',')
        names[name] = entrylist
        num = len(entrylist)
        if numsubs is None:
            numsubs = num
        elif numsubs != num:
            print namestr
            print substr
            raise ValueError, "Mismatch in number to replace"

    # now replace all keys for each of the lists
    mystr = ''
    thissub = [None]
    def namerepl(match):
        name = match.group(1)
        return names[name][thissub[0]]
    for k in range(numsubs):
        thissub[0] = k
        mystr += ("#line %d\n%s\n\n"
                  % (line, template_re.sub(namerepl, substr)))
    return mystr


_head = \
"""/*  This file was autogenerated from a template  DO NOT EDIT!!!!
       Changes should be made to the original source (.src) file
*/

"""

def get_line_header(str,beg):
    extra = []
    ind = beg-1
    char = str[ind]
    while (ind > 0) and (char != '\n'):
        extra.insert(0,char)
        ind = ind - 1
        char = str[ind]
    return ''.join(extra)

def process_str(allstr):
    newstr = allstr
    writestr = _head

    struct = parse_structure(newstr)
    #  return a (sorted) list of tuples for each begin repeat section
    #  each tuple is the start and end of a region to be template repeated

    oldend = 0
    for sub in struct:
        writestr += newstr[oldend:sub[0]]
        expanded = expand_sub(newstr[sub[1]:sub[2]],
                              newstr[sub[0]:sub[1]], sub[4])
        writestr += expanded
        oldend =  sub[3]


    writestr += newstr[oldend:]
    return writestr

include_src_re = re.compile(r"(\n|\A)#include\s*['\"]"
                            r"(?P<name>[\w\d./\\]+[.]src)['\"]", re.I)

def resolve_includes(source):
    d = os.path.dirname(source)
    fid = open(source)
    lines = []
    for line in fid.readlines():
        m = include_src_re.match(line)
        if m:
            fn = m.group('name')
            if not os.path.isabs(fn):
                fn = os.path.join(d,fn)
            if os.path.isfile(fn):
                print 'Including file',fn
                lines.extend(resolve_includes(fn))
            else:
                lines.append(line)
        else:
            lines.append(line)
    fid.close()
    return lines

def process_file(source):
    lines = resolve_includes(source)
    sourcefile = os.path.normcase(source).replace("\\","\\\\")
    return ('#line 1 "%s"\n%s'
            % (sourcefile, process_str(''.join(lines))))

if __name__ == "__main__":

    try:
        file = sys.argv[1]
    except IndexError:
        fid = sys.stdin
        outfile = sys.stdout
    else:
        fid = open(file,'r')
        (base, ext) = os.path.splitext(file)
        newname = base
        outfile = open(newname,'w')

    allstr = fid.read()
    writestr = process_str(allstr)
    outfile.write(writestr)

#!/usr/bin/env python
"""
cpuinfo

Copyright 2002 Pearu Peterson all rights reserved,
Pearu Peterson <pearu@cens.ioc.ee>
Permission to use, modify, and distribute this software is given under the
terms of the SciPy (BSD style) license.  See LICENSE.txt that came with
this distribution for specifics.

Note:  This should be merged into proc at some point.  Perhaps proc should
be returning classes like this instead of using dictionaries.

NO WARRANTY IS EXPRESSED OR IMPLIED.  USE AT YOUR OWN RISK.
$Revision: 1.1 $
$Date: 2005/04/09 19:29:34 $
Pearu Peterson
"""

__version__ = "$Id: cpuinfo.py,v 1.1 2005/04/09 19:29:34 pearu Exp $"

__all__ = ['cpu']

import sys,string,re,types

class cpuinfo_base:
    """Holds CPU information and provides methods for requiring
    the availability of various CPU features.
    """

    def _try_call(self,func):
        try:
            return func()
        except:
            pass

    def __getattr__(self,name):
        if name[0]!='_':
            if hasattr(self,'_'+name):
                attr = getattr(self,'_'+name)
                if type(attr) is types.MethodType:
                    return lambda func=self._try_call,attr=attr : func(attr)
            else:
                return lambda : None
        raise AttributeError,name

    def _getNCPUs(self):
        return 1

    def _is_32bit(self):
        return not self.is_64bit()

class linux_cpuinfo(cpuinfo_base):

    info = None

    def __init__(self):
        if self.info is not None:
            return
        info = []
        try:
            for line in open('/proc/cpuinfo').readlines():
                name_value = map(string.strip,string.split(line,':',1))
                if len(name_value)!=2:
                    continue
                name,value = name_value
                if not info or info[-1].has_key(name): # next processor
                    info.append({})
                info[-1][name] = value
            import commands
            status,output = commands.getstatusoutput('uname -m')
            if not status:
                if not info: info.append({})
                info[-1]['uname_m'] = string.strip(output)
        except:
            print sys.exc_value,'(ignoring)'
        self.__class__.info = info

    def _not_impl(self): pass

    # Athlon

    def _is_AMD(self):
        return self.info[0]['vendor_id']=='AuthenticAMD'

    def _is_AthlonK6_2(self):
        return self._is_AMD() and self.info[0]['model'] == '2'

    def _is_AthlonK6_3(self):
        return self._is_AMD() and self.info[0]['model'] == '3'

    def _is_AthlonK6(self):
        return re.match(r'.*?AMD-K6',self.info[0]['model name']) is not None

    def _is_AthlonK7(self):
        return re.match(r'.*?AMD-K7',self.info[0]['model name']) is not None

    def _is_AthlonMP(self):
        return re.match(r'.*?Athlon\(tm\) MP\b',
                        self.info[0]['model name']) is not None

    def _is_Athlon64(self):
        return re.match(r'.*?Athlon\(tm\) 64\b',
                        self.info[0]['model name']) is not None

    def _is_AthlonHX(self):
        return re.match(r'.*?Athlon HX\b',
                        self.info[0]['model name']) is not None

    def _is_Opteron(self):
        return re.match(r'.*?Opteron\b',
                        self.info[0]['model name']) is not None

    def _is_Hammer(self):
        return re.match(r'.*?Hammer\b',
                        self.info[0]['model name']) is not None

    # Alpha

    def _is_Alpha(self):
        return self.info[0]['cpu']=='Alpha'

    def _is_EV4(self):
        return self.is_Alpha() and self.info[0]['cpu model'] == 'EV4'

    def _is_EV5(self):
        return self.is_Alpha() and self.info[0]['cpu model'] == 'EV5'

    def _is_EV56(self):
        return self.is_Alpha() and self.info[0]['cpu model'] == 'EV56'

    def _is_PCA56(self):
        return self.is_Alpha() and self.info[0]['cpu model'] == 'PCA56'

    # Intel

    #XXX
    _is_i386 = _not_impl

    def _is_Intel(self):
        return self.info[0]['vendor_id']=='GenuineIntel'

    def _is_i486(self):
        return self.info[0]['cpu']=='i486'

    def _is_i586(self):
        return self.is_Intel() and self.info[0]['cpu family'] == '5'

    def _is_i686(self):
        return self.is_Intel() and self.info[0]['cpu family'] == '6'

    def _is_Celeron(self):
        return re.match(r'.*?Celeron',
                        self.info[0]['model name']) is not None

    def _is_Pentium(self):
        return re.match(r'.*?Pentium',
                        self.info[0]['model name']) is not None

    def _is_PentiumII(self):
        return re.match(r'.*?Pentium.*?II\b',
                        self.info[0]['model name']) is not None

    def _is_PentiumPro(self):
        return re.match(r'.*?PentiumPro\b',
                        self.info[0]['model name']) is not None

    def _is_PentiumMMX(self):
        return re.match(r'.*?Pentium.*?MMX\b',
                        self.info[0]['model name']) is not None

    def _is_PentiumIII(self):
        return re.match(r'.*?Pentium.*?III\b',
                        self.info[0]['model name']) is not None

    def _is_PentiumIV(self):
        return re.match(r'.*?Pentium.*?(IV|4)\b',
                        self.info[0]['model name']) is not None

    def _is_PentiumM(self):
        return re.match(r'.*?Pentium.*?M\b',
                        self.info[0]['model name']) is not None

    def _is_Prescott(self):
        return self.is_PentiumIV() and self.has_sse3()

    def _is_Nocona(self):
        return self.is_PentiumIV() and self.is_64bit()

    def _is_Itanium(self):
        return re.match(r'.*?Itanium\b',
                        self.info[0]['family']) is not None

    def _is_XEON(self):
        return re.match(r'.*?XEON\b',
                        self.info[0]['model name'],re.IGNORECASE) is not None

    _is_Xeon = _is_XEON

    # Varia

    def _is_singleCPU(self):
        return len(self.info) == 1

    def _getNCPUs(self):
        return len(self.info)

    def _has_fdiv_bug(self):
        return self.info[0]['fdiv_bug']=='yes'

    def _has_f00f_bug(self):
        return self.info[0]['f00f_bug']=='yes'

    def _has_mmx(self):
        return re.match(r'.*?\bmmx\b',self.info[0]['flags']) is not None

    def _has_sse(self):
        return re.match(r'.*?\bsse\b',self.info[0]['flags']) is not None

    def _has_sse2(self):
        return re.match(r'.*?\bsse2\b',self.info[0]['flags']) is not None

    def _has_sse3(self):
        return re.match(r'.*?\bsse3\b',self.info[0]['flags']) is not None

    def _has_3dnow(self):
        return re.match(r'.*?\b3dnow\b',self.info[0]['flags']) is not None

    def _has_3dnowext(self):
        return re.match(r'.*?\b3dnowext\b',self.info[0]['flags']) is not None

    def _is_64bit(self):
        if self.is_Alpha():
            return True
        if self.info[0].get('clflush size','')=='64':
            return True
        if self.info[0].get('uname_m','')=='x86_64':
            return True
        if self.info[0].get('arch','')=='IA-64':
            return True
        return False

    def _is_32bit(self):
        return not self.is_64bit()

class irix_cpuinfo(cpuinfo_base):

    info = None

    def __init__(self):
        if self.info is not None:
            return
        info = []
        try:
            import commands
            status,output = commands.getstatusoutput('sysconf')
            if status not in [0,256]:
                return
            for line in output.split('\n'):
                name_value = map(string.strip,string.split(line,' ',1))
                if len(name_value)!=2:
                    continue
                name,value = name_value
                if not info:
                    info.append({})
                info[-1][name] = value
        except:
            print sys.exc_value,'(ignoring)'
        self.__class__.info = info

        #print info
    def _not_impl(self): pass

    def _is_singleCPU(self):
        return self.info[0].get('NUM_PROCESSORS') == '1'

    def _getNCPUs(self):
        return int(self.info[0].get('NUM_PROCESSORS'))

    def __cputype(self,n):
        return self.info[0].get('PROCESSORS').split()[0].lower() == 'r%s' % (n)
    def _is_r2000(self): return self.__cputype(2000)
    def _is_r3000(self): return self.__cputype(3000)
    def _is_r3900(self): return self.__cputype(3900)
    def _is_r4000(self): return self.__cputype(4000)
    def _is_r4100(self): return self.__cputype(4100)
    def _is_r4300(self): return self.__cputype(4300)
    def _is_r4400(self): return self.__cputype(4400)
    def _is_r4600(self): return self.__cputype(4600)
    def _is_r4650(self): return self.__cputype(4650)
    def _is_r5000(self): return self.__cputype(5000)
    def _is_r6000(self): return self.__cputype(6000)
    def _is_r8000(self): return self.__cputype(8000)
    def _is_r10000(self): return self.__cputype(10000)
    def _is_r12000(self): return self.__cputype(12000)
    def _is_rorion(self): return self.__cputype('orion')

    def get_ip(self):
        try: return self.info[0].get('MACHINE')
        except: pass
    def __machine(self,n):
        return self.info[0].get('MACHINE').lower() == 'ip%s' % (n)
    def _is_IP19(self): return self.__machine(19)
    def _is_IP20(self): return self.__machine(20)
    def _is_IP21(self): return self.__machine(21)
    def _is_IP22(self): return self.__machine(22)
    def _is_IP22_4k(self): return self.__machine(22) and self._is_r4000()
    def _is_IP22_5k(self): return self.__machine(22)  and self._is_r5000()
    def _is_IP24(self): return self.__machine(24)
    def _is_IP25(self): return self.__machine(25)
    def _is_IP26(self): return self.__machine(26)
    def _is_IP27(self): return self.__machine(27)
    def _is_IP28(self): return self.__machine(28)
    def _is_IP30(self): return self.__machine(30)
    def _is_IP32(self): return self.__machine(32)
    def _is_IP32_5k(self): return self.__machine(32) and self._is_r5000()
    def _is_IP32_10k(self): return self.__machine(32) and self._is_r10000()

class darwin_cpuinfo(cpuinfo_base):

    info = None

    def __init__(self):
        if self.info is not None:
            return
        info = []
        try:
            import commands
            status,output = commands.getstatusoutput('arch')
            if not status:
                if not info: info.append({})
                info[-1]['arch'] = string.strip(output)
            status,output = commands.getstatusoutput('machine')
            if not status:
                if not info: info.append({})
                info[-1]['machine'] = string.strip(output)
            status,output = commands.getstatusoutput('sysctl hw')
            if not status:
                if not info: info.append({})
                d = {}
                for l in string.split(output,'\n'):
                    l = map(string.strip,string.split(l, '='))
                    if len(l)==2:
                        d[l[0]]=l[1]
                info[-1]['sysctl_hw'] = d
        except:
            print sys.exc_value,'(ignoring)'
        self.__class__.info = info

    def _not_impl(self): pass

    def _getNCPUs(self):
        try: return int(self.info[0]['sysctl_hw']['hw.ncpu'])
        except: return 1

    def _is_Power_Macintosh(self):
        return self.info[0]['sysctl_hw']['hw.machine']=='Power Macintosh'

    def _is_i386(self):
        return self.info[0]['arch']=='i386'
    def _is_ppc(self):
        return self.info[0]['arch']=='ppc'

    def __machine(self,n):
        return self.info[0]['machine'] == 'ppc%s'%n
    def _is_ppc601(self): return self.__machine(601)
    def _is_ppc602(self): return self.__machine(602)
    def _is_ppc603(self): return self.__machine(603)
    def _is_ppc603e(self): return self.__machine('603e')
    def _is_ppc604(self): return self.__machine(604)
    def _is_ppc604e(self): return self.__machine('604e')
    def _is_ppc620(self): return self.__machine(620)
    def _is_ppc630(self): return self.__machine(630)
    def _is_ppc740(self): return self.__machine(740)
    def _is_ppc7400(self): return self.__machine(7400)
    def _is_ppc7450(self): return self.__machine(7450)
    def _is_ppc750(self): return self.__machine(750)
    def _is_ppc403(self): return self.__machine(403)
    def _is_ppc505(self): return self.__machine(505)
    def _is_ppc801(self): return self.__machine(801)
    def _is_ppc821(self): return self.__machine(821)
    def _is_ppc823(self): return self.__machine(823)
    def _is_ppc860(self): return self.__machine(860)

class sunos_cpuinfo(cpuinfo_base):

    info = None

    def __init__(self):
        if self.info is not None:
            return
        info = []
        try:
            import commands
            status,output = commands.getstatusoutput('arch')
            if not status:
                if not info: info.append({})
                info[-1]['arch'] = string.strip(output)
            status,output = commands.getstatusoutput('mach')
            if not status:
                if not info: info.append({})
                info[-1]['mach'] = string.strip(output)
            status,output = commands.getstatusoutput('uname -i')
            if not status:
                if not info: info.append({})
                info[-1]['uname_i'] = string.strip(output)
            status,output = commands.getstatusoutput('uname -X')
            if not status:
                if not info: info.append({})
                d = {}
                for l in string.split(output,'\n'):
                    l = map(string.strip,string.split(l, '='))
                    if len(l)==2:
                        d[l[0]]=l[1]
                info[-1]['uname_X'] = d
            status,output = commands.getstatusoutput('isainfo -b')
            if not status:
                if not info: info.append({})
                info[-1]['isainfo_b'] = string.strip(output)
            status,output = commands.getstatusoutput('isainfo -n')
            if not status:
                if not info: info.append({})
                info[-1]['isainfo_n'] = string.strip(output)
            status,output = commands.getstatusoutput('psrinfo -v 0')
            if not status:
                if not info: info.append({})
                for l in string.split(output,'\n'):
                    m = re.match(r'\s*The (?P<p>[\w\d]+) processor operates at',l)
                    if m:
                        info[-1]['processor'] = m.group('p')
                        break
        except:
            print sys.exc_value,'(ignoring)'
        self.__class__.info = info

    def _not_impl(self): pass

    def _is_32bit(self):
        return self.info[0]['isainfo_b']=='32'
    def _is_64bit(self):
        return self.info[0]['isainfo_b']=='64'

    def _is_i386(self):
        return self.info[0]['isainfo_n']=='i386'
    def _is_sparc(self):
        return self.info[0]['isainfo_n']=='sparc'
    def _is_sparcv9(self):
        return self.info[0]['isainfo_n']=='sparcv9'

    def _getNCPUs(self):
        try: return int(self.info[0]['uname_X']['NumCPU'])
        except: return 1

    def _is_sun4(self):
        return self.info[0]['arch']=='sun4'

    def _is_SUNW(self):
        return re.match(r'SUNW',self.info[0]['uname_i']) is not None
    def _is_sparcstation5(self):
        return re.match(r'.*SPARCstation-5',self.info[0]['uname_i']) is not None
    def _is_ultra1(self):
        return re.match(r'.*Ultra-1',self.info[0]['uname_i']) is not None
    def _is_ultra250(self):
        return re.match(r'.*Ultra-250',self.info[0]['uname_i']) is not None
    def _is_ultra2(self):
        return re.match(r'.*Ultra-2',self.info[0]['uname_i']) is not None
    def _is_ultra30(self):
        return re.match(r'.*Ultra-30',self.info[0]['uname_i']) is not None
    def _is_ultra4(self):
        return re.match(r'.*Ultra-4',self.info[0]['uname_i']) is not None
    def _is_ultra5_10(self):
        return re.match(r'.*Ultra-5_10',self.info[0]['uname_i']) is not None
    def _is_ultra5(self):
        return re.match(r'.*Ultra-5',self.info[0]['uname_i']) is not None
    def _is_ultra60(self):
        return re.match(r'.*Ultra-60',self.info[0]['uname_i']) is not None
    def _is_ultra80(self):
        return re.match(r'.*Ultra-80',self.info[0]['uname_i']) is not None
    def _is_ultraenterprice(self):
        return re.match(r'.*Ultra-Enterprise',self.info[0]['uname_i']) is not None
    def _is_ultraenterprice10k(self):
        return re.match(r'.*Ultra-Enterprise-10000',self.info[0]['uname_i']) is not None
    def _is_sunfire(self):
        return re.match(r'.*Sun-Fire',self.info[0]['uname_i']) is not None
    def _is_ultra(self):
        return re.match(r'.*Ultra',self.info[0]['uname_i']) is not None

    def _is_cpusparcv7(self):
        return self.info[0]['processor']=='sparcv7'
    def _is_cpusparcv8(self):
        return self.info[0]['processor']=='sparcv8'
    def _is_cpusparcv9(self):
        return self.info[0]['processor']=='sparcv9'

class win32_cpuinfo(cpuinfo_base):

    info = None
    pkey = "HARDWARE\\DESCRIPTION\\System\\CentralProcessor"
    # XXX: what does the value of
    #   HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System\CentralProcessor\0
    # mean?

    def __init__(self):
        if self.info is not None:
            return
        info = []
        try:
            #XXX: Bad style to use so long `try:...except:...`. Fix it!
            import _winreg
            pkey = "HARDWARE\\DESCRIPTION\\System\\CentralProcessor"
            prgx = re.compile(r"family\s+(?P<FML>\d+)\s+model\s+(?P<MDL>\d+)"\
                              "\s+stepping\s+(?P<STP>\d+)",re.IGNORECASE)
            chnd=_winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,pkey)
            pnum=0
            while 1:
                try:
                    proc=_winreg.EnumKey(chnd,pnum)
                except _winreg.error:
                    break
                else:
                    pnum+=1
                    print proc
                    info.append({"Processor":proc})
                    phnd=_winreg.OpenKey(chnd,proc)
                    pidx=0
                    while True:
                        try:
                            name,value,vtpe=_winreg.EnumValue(phnd,pidx)
                        except _winreg.error:
                            break
                        else:
                            pidx=pidx+1
                            info[-1][name]=value
                            if name=="Identifier":
                                srch=prgx.search(value)
                                if srch:
                                    info[-1]["Family"]=int(srch.group("FML"))
                                    info[-1]["Model"]=int(srch.group("MDL"))
                                    info[-1]["Stepping"]=int(srch.group("STP"))
        except:
            print sys.exc_value,'(ignoring)'
        self.__class__.info = info

    def _not_impl(self): pass

    # Athlon

    def _is_AMD(self):
        return self.info[0]['VendorIdentifier']=='AuthenticAMD'

    def _is_Am486(self):
        return self.is_AMD() and self.info[0]['Family']==4

    def _is_Am5x86(self):
        return self.is_AMD() and self.info[0]['Family']==4

    def _is_AMDK5(self):
        return self.is_AMD() and self.info[0]['Family']==5 \
               and self.info[0]['Model'] in [0,1,2,3]

    def _is_AMDK6(self):
        return self.is_AMD() and self.info[0]['Family']==5 \
               and self.info[0]['Model'] in [6,7]

    def _is_AMDK6_2(self):
        return self.is_AMD() and self.info[0]['Family']==5 \
               and self.info[0]['Model']==8

    def _is_AMDK6_3(self):
        return self.is_AMD() and self.info[0]['Family']==5 \
               and self.info[0]['Model']==9

    def _is_Athlon(self):
        return self.is_AMD() and self.info[0]['Family']==6

    def _is_Athlon64(self):
        return self.is_AMD() and self.info[0]['Family']==15 \
               and self.info[0]['Model']==4

    def _is_Opteron(self):
        return self.is_AMD() and self.info[0]['Family']==15 \
               and self.info[0]['Model']==5

    # Intel

    def _is_Intel(self):
        return self.info[0]['VendorIdentifier']=='GenuineIntel'

    def _is_i386(self):
        return self.info[0]['Family']==3

    def _is_i486(self):
        return self.info[0]['Family']==4

    def _is_i586(self):
        return self.is_Intel() and self.info[0]['Family']==5

    def _is_i686(self):
        return self.is_Intel() and self.info[0]['Family']==6

    def _is_Pentium(self):
        return self.is_Intel() and self.info[0]['Family']==5

    def _is_PentiumMMX(self):
        return self.is_Intel() and self.info[0]['Family']==5 \
               and self.info[0]['Model']==4

    def _is_PentiumPro(self):
        return self.is_Intel() and self.info[0]['Family']==6 \
               and self.info[0]['Model']==1

    def _is_PentiumII(self):
        return self.is_Intel() and self.info[0]['Family']==6 \
               and self.info[0]['Model'] in [3,5,6]

    def _is_PentiumIII(self):
        return self.is_Intel() and self.info[0]['Family']==6 \
               and self.info[0]['Model'] in [7,8,9,10,11]

    def _is_PentiumIV(self):
        return self.is_Intel() and self.info[0]['Family']==15

    # Varia

    def _is_singleCPU(self):
        return len(self.info) == 1

    def _getNCPUs(self):
        return len(self.info)

    def _has_mmx(self):
        if self.is_Intel():
            return (self.info[0]['Family']==5 and self.info[0]['Model']==4) \
                   or (self.info[0]['Family'] in [6,15])
        elif self.is_AMD():
            return self.info[0]['Family'] in [5,6,15]

    def _has_sse(self):
        if self.is_Intel():
            return (self.info[0]['Family']==6 and \
                    self.info[0]['Model'] in [7,8,9,10,11]) \
                    or self.info[0]['Family']==15
        elif self.is_AMD():
            return (self.info[0]['Family']==6 and \
                    self.info[0]['Model'] in [6,7,8,10]) \
                    or self.info[0]['Family']==15

    def _has_sse2(self):
        return self.info[0]['Family']==15

    def _has_3dnow(self):
        # XXX: does only AMD have 3dnow??
        return self.is_AMD() and self.info[0]['Family'] in [5,6,15]

    def _has_3dnowext(self):
        return self.is_AMD() and self.info[0]['Family'] in [6,15]

if sys.platform[:5] == 'linux': # variations: linux2,linux-i386 (any others?)
    cpuinfo = linux_cpuinfo
elif sys.platform[:4] == 'irix':
    cpuinfo = irix_cpuinfo
elif sys.platform == 'darwin':
    cpuinfo = darwin_cpuinfo
elif sys.platform[:5] == 'sunos':
    cpuinfo = sunos_cpuinfo
elif sys.platform[:5] == 'win32':
    cpuinfo = win32_cpuinfo
elif sys.platform[:6] == 'cygwin':
    cpuinfo = linux_cpuinfo
#XXX: other OS's. Eg. use _winreg on Win32. Or os.uname on unices.
else:
    cpuinfo = cpuinfo_base

cpu = cpuinfo()

if __name__ == "__main__":

    cpu.is_blaa()
    cpu.is_Intel()
    cpu.is_Alpha()

    print 'CPU information:',
    for name in dir(cpuinfo):
        if name[0]=='_' and name[1]!='_':
            r = getattr(cpu,name[1:])()
            if r:
                if r!=1:
                    print '%s=%s' %(name[1:],r),
                else:
                    print name[1:],
    print

import re
import os
import sys
import new

from distutils.ccompiler import *
from distutils import ccompiler
from distutils.sysconfig import customize_compiler
from distutils.version import LooseVersion

import log
from exec_command import exec_command
from misc_util import cyg2win32, is_sequence, mingw32
from distutils.spawn import _nt_quote_args

# hack to set compiler optimizing options. Needs to integrated with something.
import distutils.sysconfig
_old_init_posix = distutils.sysconfig._init_posix
def _new_init_posix():
    _old_init_posix()
    distutils.sysconfig._config_vars['OPT'] = '-Wall -g -O0'
#distutils.sysconfig._init_posix = _new_init_posix

# Using customized CCompiler.spawn.
def CCompiler_spawn(self, cmd, display=None):
    if display is None:
        display = cmd
        if is_sequence(display):
            display = ' '.join(list(display))
    log.info(display)
    if is_sequence(cmd) and os.name == 'nt':
        cmd = _nt_quote_args(list(cmd))
    s,o = exec_command(cmd)
    if s:
        if is_sequence(cmd):
            cmd = ' '.join(list(cmd))
        print o
        raise DistutilsExecError,\
              'Command "%s" failed with exit status %d' % (cmd, s)
CCompiler.spawn = new.instancemethod(CCompiler_spawn,None,CCompiler)

def CCompiler_object_filenames(self, source_filenames, strip_dir=0, output_dir=''):
    if output_dir is None:
        output_dir = ''
    obj_names = []
    for src_name in source_filenames:
        base, ext = os.path.splitext(os.path.normpath(src_name))
        base = os.path.splitdrive(base)[1] # Chop off the drive
        base = base[os.path.isabs(base):]  # If abs, chop off leading /
        if base.startswith('..'):
            # Resolve starting relative path components, middle ones
            # (if any) have been handled by os.path.normpath above.
            i = base.rfind('..')+2
            d = base[:i]
            d = os.path.basename(os.path.abspath(d))
            base = d + base[i:]
        if ext not in self.src_extensions:
            raise UnknownFileError, \
                  "unknown file type '%s' (from '%s')" % (ext, src_name)
        if strip_dir:
            base = os.path.basename(base)
        obj_name = os.path.join(output_dir,base + self.obj_extension)
        obj_names.append(obj_name)
    return obj_names

CCompiler.object_filenames = new.instancemethod(CCompiler_object_filenames,
                                                None,CCompiler)

def CCompiler_compile(self, sources, output_dir=None, macros=None,
                      include_dirs=None, debug=0, extra_preargs=None,
                      extra_postargs=None, depends=None):
    # This method is effective only with Python >=2.3 distutils.
    # Any changes here should be applied also to fcompiler.compile
    # method to support pre Python 2.3 distutils.
    if not sources:
        return []
    from fcompiler import FCompiler
    if isinstance(self, FCompiler):
        display = []
        for fc in ['f77','f90','fix']:
            fcomp = getattr(self,'compiler_'+fc)
            if fcomp is None:
                continue
            display.append("Fortran %s compiler: %s" % (fc, ' '.join(fcomp)))
        display = '\n'.join(display)
    else:
        ccomp = self.compiler_so
        display = "C compiler: %s\n" % (' '.join(ccomp),)
    log.info(display)
    macros, objects, extra_postargs, pp_opts, build = \
            self._setup_compile(output_dir, macros, include_dirs, sources,
                                depends, extra_postargs)
    cc_args = self._get_cc_args(pp_opts, debug, extra_preargs)
    display = "compile options: '%s'" % (' '.join(cc_args))
    if extra_postargs:
        display += "\nextra options: '%s'" % (' '.join(extra_postargs))
    log.info(display)

    # build any sources in same order as they were originally specified
    #   especially important for fortran .f90 files using modules
    if isinstance(self, FCompiler):
        objects_to_build = build.keys()
        for obj in objects:
            if obj in objects_to_build:
                src, ext = build[obj]
                if self.compiler_type=='absoft':
                    obj = cyg2win32(obj)
                    src = cyg2win32(src)
                self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)
    else:
        for obj, (src, ext) in build.items():
            self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)

    # Return *all* object filenames, not just the ones we just built.
    return objects

CCompiler.compile = new.instancemethod(CCompiler_compile,None,CCompiler)

def CCompiler_customize_cmd(self, cmd):
    """ Customize compiler using distutils command.
    """
    log.info('customize %s using %s' % (self.__class__.__name__,
                                        cmd.__class__.__name__))
    if getattr(cmd,'include_dirs',None) is not None:
        self.set_include_dirs(cmd.include_dirs)
    if getattr(cmd,'define',None) is not None:
        for (name,value) in cmd.define:
            self.define_macro(name, value)
    if getattr(cmd,'undef',None) is not None:
        for macro in cmd.undef:
            self.undefine_macro(macro)
    if getattr(cmd,'libraries',None) is not None:
        self.set_libraries(self.libraries + cmd.libraries)
    if getattr(cmd,'library_dirs',None) is not None:
        self.set_library_dirs(self.library_dirs + cmd.library_dirs)
    if getattr(cmd,'rpath',None) is not None:
        self.set_runtime_library_dirs(cmd.rpath)
    if getattr(cmd,'link_objects',None) is not None:
        self.set_link_objects(cmd.link_objects)
    return

CCompiler.customize_cmd = new.instancemethod(\
    CCompiler_customize_cmd,None,CCompiler)

def _compiler_to_string(compiler):
    props = []
    mx = 0
    keys = compiler.executables.keys()
    for key in ['version','libraries','library_dirs',
                'object_switch','compile_switch',
                'include_dirs','define','undef','rpath','link_objects']:
        if key not in keys:
            keys.append(key)
    for key in keys:
        if hasattr(compiler,key):
            v = getattr(compiler, key)
            mx = max(mx,len(key))
            props.append((key,repr(v)))
    lines = []
    format = '%-' + repr(mx+1) + 's = %s'
    for prop in props:
        lines.append(format % prop)
    return '\n'.join(lines)

def CCompiler_show_customization(self):
    if 0:
        for attrname in ['include_dirs','define','undef',
                         'libraries','library_dirs',
                         'rpath','link_objects']:
            attr = getattr(self,attrname,None)
            if not attr:
                continue
            log.info("compiler '%s' is set to %s" % (attrname,attr))
    try: self.get_version()
    except: pass
    if log._global_log.threshold<2:
        print '*'*80
        print self.__class__
        print _compiler_to_string(self)
        print '*'*80

CCompiler.show_customization = new.instancemethod(\
    CCompiler_show_customization,None,CCompiler)


def CCompiler_customize(self, dist, need_cxx=0):
    # See FCompiler.customize for suggested usage.
    log.info('customize %s' % (self.__class__.__name__))
    customize_compiler(self)
    if need_cxx:
        # In general, distutils uses -Wstrict-prototypes, but this option is
        # not valid for C++ code, only for C.  Remove it if it's there to
        # avoid a spurious warning on every compilation.  All the default
        # options used by distutils can be extracted with:
        
        # from distutils import sysconfig
        # sysconfig.get_config_vars('CC', 'CXX', 'OPT', 'BASECFLAGS',
        # 'CCSHARED', 'LDSHARED', 'SO')
        try:
            self.compiler_so.remove('-Wstrict-prototypes')
        except ValueError:
            pass
        
        if hasattr(self,'compiler') and self.compiler[0].find('cc')>=0:
            if not self.compiler_cxx:
                if self.compiler[0][:3] == 'gcc':
                    a, b = 'gcc', 'g++'
                else:
                    a, b = 'cc', 'c++'
                self.compiler_cxx = [self.compiler[0].replace(a,b)]\
                                    + self.compiler[1:]
        else:
            if hasattr(self,'compiler'):
                 log.warn("#### %s #######" % (self.compiler,))
            log.warn('Missing compiler_cxx fix for '+self.__class__.__name__)
    return

CCompiler.customize = new.instancemethod(\
    CCompiler_customize,None,CCompiler)

def simple_version_match(pat=r'[-.\d]+', ignore=None, start=''):
    def matcher(self, version_string):
        pos = 0
        if start:
            m = re.match(start, version_string)
            if not m:
                return None
            pos = m.end()
        while 1:
            m = re.search(pat, version_string[pos:])
            if not m:
                return None
            if ignore and re.match(ignore, m.group(0)):
                pos = m.end()
                continue
            break
        return m.group(0)
    return matcher

def CCompiler_get_version(self, force=0, ok_status=[0]):
    """ Compiler version. Returns None if compiler is not available. """
    if not force and hasattr(self,'version'):
        return self.version
    try:
        version_cmd = self.version_cmd
    except AttributeError:
        return None
    cmd = ' '.join(version_cmd)
    try:
        matcher = self.version_match
    except AttributeError:
        try:
            pat = self.version_pattern
        except AttributeError:
            return None
        def matcher(version_string):
            m = re.match(pat, version_string)
            if not m:
                return None
            version = m.group('version')
            return version

    status, output = exec_command(cmd,use_tee=0)
    version = None
    if status in ok_status:
        version = matcher(output)
        if not version:
            log.warn("Couldn't match compiler version for %r" % (output,))
        else:
            version = LooseVersion(version)
    self.version = version
    return version

CCompiler.get_version = new.instancemethod(\
    CCompiler_get_version,None,CCompiler)

compiler_class['intel'] = ('intelccompiler','IntelCCompiler',
                           "Intel C Compiler for 32-bit applications")
compiler_class['intele'] = ('intelccompiler','IntelItaniumCCompiler',
                           "Intel C Itanium Compiler for Itanium-based applications")
ccompiler._default_compilers = ccompiler._default_compilers \
                               + (('linux.*','intel'),('linux.*','intele'))

if sys.platform == 'win32':
    compiler_class['mingw32'] = ('mingw32ccompiler', 'Mingw32CCompiler',
                                 "Mingw32 port of GNU C Compiler for Win32"\
                                 "(for MSC built Python)")
    if mingw32():
        # On windows platforms, we want to default to mingw32 (gcc)
        # because msvc can't build blitz stuff.
        log.info('Setting mingw32 as default compiler for nt.')
        ccompiler._default_compilers = (('nt', 'mingw32'),) \
                                       + ccompiler._default_compilers


_distutils_new_compiler = new_compiler
def new_compiler (plat=None,
                  compiler=None,
                  verbose=0,
                  dry_run=0,
                  force=0):
    # Try first C compilers from numpy.distutils.
    if plat is None:
        plat = os.name
    try:
        if compiler is None:
            compiler = get_default_compiler(plat)
        (module_name, class_name, long_description) = compiler_class[compiler]
    except KeyError:
        msg = "don't know how to compile C/C++ code on platform '%s'" % plat
        if compiler is not None:
            msg = msg + " with '%s' compiler" % compiler
        raise DistutilsPlatformError, msg
    module_name = "numpy.distutils." + module_name
    try:
        __import__ (module_name)
    except ImportError, msg:
        log.info('%s in numpy.distutils; trying from distutils',
                 str(msg))
        module_name = module_name[6:]
        try:
            __import__(module_name)
        except ImportError, msg:
            raise DistutilsModuleError, \
                  "can't compile C/C++ code: unable to load module '%s'" % \
                  module_name
    try:
        module = sys.modules[module_name]
        klass = vars(module)[class_name]
    except KeyError:
        raise DistutilsModuleError, \
              ("can't compile C/C++ code: unable to find class '%s' " +
               "in module '%s'") % (class_name, module_name)
    compiler = klass(None, dry_run, force)
    log.debug('new_compiler returns %s' % (klass))
    return compiler

ccompiler.new_compiler = new_compiler


_distutils_gen_lib_options = gen_lib_options
def gen_lib_options(compiler, library_dirs, runtime_library_dirs, libraries):
    r = _distutils_gen_lib_options(compiler, library_dirs,
                                   runtime_library_dirs, libraries)
    lib_opts = []
    for i in r:
        if is_sequence(i):
            lib_opts.extend(list(i))
        else:
            lib_opts.append(i)
    return lib_opts
ccompiler.gen_lib_options = gen_lib_options


##Fix distutils.util.split_quoted:
import re,string
_wordchars_re = re.compile(r'[^\\\'\"%s ]*' % string.whitespace)
_squote_re = re.compile(r"'(?:[^'\\]|\\.)*'")
_dquote_re = re.compile(r'"(?:[^"\\]|\\.)*"')
_has_white_re = re.compile(r'\s')
def split_quoted(s):
    s = string.strip(s)
    words = []
    pos = 0

    while s:
        m = _wordchars_re.match(s, pos)
        end = m.end()
        if end == len(s):
            words.append(s[:end])
            break

        if s[end] in string.whitespace: # unescaped, unquoted whitespace: now
            words.append(s[:end])       # we definitely have a word delimiter
            s = string.lstrip(s[end:])
            pos = 0

        elif s[end] == '\\':            # preserve whatever is being escaped;
                                        # will become part of the current word
            s = s[:end] + s[end+1:]
            pos = end+1

        else:
            if s[end] == "'":           # slurp singly-quoted string
                m = _squote_re.match(s, end)
            elif s[end] == '"':         # slurp doubly-quoted string
                m = _dquote_re.match(s, end)
            else:
                raise RuntimeError, \
                      "this can't happen (bad char '%c')" % s[end]

            if m is None:
                raise ValueError, \
                      "bad string (mismatched %s quotes?)" % s[end]

            (beg, end) = m.span()
            if _has_white_re.search(s[beg+1:end-1]):
                s = s[:beg] + s[beg+1:end-1] + s[end:]
                pos = m.end() - 2
            else:
                # Keeping quotes when a quoted word does not contain
                # white-space. XXX: send a patch to distutils
                pos = m.end()

        if pos >= len(s):
            words.append(s)
            break

    return words
ccompiler.split_quoted = split_quoted

import os
import re
import sys
import imp
import copy
import glob

try:
    set
except NameError:
    from sets import Set as set

__all__ = ['Configuration', 'get_numpy_include_dirs', 'default_config_dict',
           'dict_append', 'appendpath', 'generate_config_py',
           'get_cmd', 'allpath', 'get_mathlibs',
           'terminal_has_colors', 'red_text', 'green_text', 'yellow_text',
           'blue_text', 'cyan_text', 'cyg2win32','mingw32','all_strings',
           'has_f_sources', 'has_cxx_sources', 'filter_sources',
           'get_dependencies', 'is_local_src_dir', 'get_ext_source_files',
           'get_script_files', 'get_lib_source_files', 'get_data_files',
           'dot_join', 'get_frame', 'minrelpath','njoin',
           'is_sequence', 'is_string', 'as_list', 'gpaths']

def allpath(name):
    "Convert a /-separated pathname to one using the OS's path separator."
    splitted = name.split('/')
    return os.path.join(*splitted)

def rel_path(path, parent_path):
    """ Return path relative to parent_path.
    """
    pd = os.path.abspath(parent_path)
    apath = os.path.abspath(path)
    if len(apath)<len(pd):
        return path
    if apath==pd:
        return ''
    if pd == apath[:len(pd)]:
        assert apath[len(pd)] in [os.sep],`path,apath[len(pd)]`
        path = apath[len(pd)+1:]
    return path

def get_path(mod_name, parent_path=None):
    """ Return path of the module.

    Returned path is relative to parent_path when given,
    otherwise it is absolute path.
    """
    if mod_name == '__builtin__':
        #builtin if/then added by Pearu for use in core.run_setup.
        d = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        __import__(mod_name)
        mod = sys.modules[mod_name]
        if hasattr(mod,'__file__'):
            filename = mod.__file__
            d = os.path.dirname(os.path.abspath(mod.__file__))
        else:
            # we're probably running setup.py as execfile("setup.py")
            # (likely we're building an egg)
            d = os.path.abspath('.')
            # hmm, should we use sys.argv[0] like in __builtin__ case?

    if parent_path is not None:
        d = rel_path(d, parent_path)
    return d or '.'

def njoin(*path):
    """ Join two or more pathname components +
    - convert a /-separated pathname to one using the OS's path separator.
    - resolve `..` and `.` from path.

    Either passing n arguments as in njoin('a','b'), or a sequence
    of n names as in njoin(['a','b']) is handled, or a mixture of such arguments.
    """
    paths = []
    for p in path:
        if is_sequence(p):
            # njoin(['a', 'b'], 'c')
            paths.append(njoin(*p))
        else:
            assert is_string(p)
            paths.append(p)
    path = paths
    if not path:
        # njoin()
        joined = ''
    else:
        # njoin('a', 'b')
        joined = os.path.join(*path)
    if os.path.sep != '/':
        joined = joined.replace('/',os.path.sep)
    return minrelpath(joined)

def get_mathlibs(path=None):
    """ Return the MATHLIB line from config.h
    """
    if path is None:
        path = get_numpy_include_dirs()[0]
    config_file = os.path.join(path,'config.h')
    fid = open(config_file)
    mathlibs = []
    s = '#define MATHLIB'
    for line in fid.readlines():
        if line.startswith(s):
            value = line[len(s):].strip()
            if value:
                mathlibs.extend(value.split(','))
    fid.close()
    return mathlibs

def minrelpath(path):
    """ Resolve `..` and '.' from path.
    """
    if not is_string(path):
        return path
    if '.' not in path:
        return path
    l = path.split(os.sep)
    while l:
        try:
            i = l.index('.',1)
        except ValueError:
            break
        del l[i]
    j = 1
    while l:
        try:
            i = l.index('..',j)
        except ValueError:
            break
        if l[i-1]=='..':
            j += 1
        else:
            del l[i],l[i-1]
            j = 1
    if not l:
        return ''
    return os.sep.join(l)

def _fix_paths(paths,local_path,include_non_existing):
    assert is_sequence(paths), repr(type(paths))
    new_paths = []
    assert not is_string(paths),`paths`
    for n in paths:
        if is_string(n):
            if '*' in n or '?' in n:
                p = glob.glob(n)
                p2 = glob.glob(njoin(local_path,n))
                if p2:
                    new_paths.extend(p2)
                elif p:
                    new_paths.extend(p)
                else:
                    if include_non_existing:
                        new_paths.append(n)
                    print 'could not resolve pattern in %r: %r' \
                              % (local_path,n)
            else:
                n2 = njoin(local_path,n)
                if os.path.exists(n2):
                    new_paths.append(n2)
                else:
                    if os.path.exists(n):
                        new_paths.append(n)
                    elif include_non_existing:
                        new_paths.append(n)
                    if not os.path.exists(n):
                        print 'non-existing path in %r: %r' \
                              % (local_path,n)

        elif is_sequence(n):
            new_paths.extend(_fix_paths(n,local_path,include_non_existing))
        else:
            new_paths.append(n)
    return map(minrelpath,new_paths)

def gpaths(paths, local_path='', include_non_existing=True):
    """ Apply glob to paths and prepend local_path if needed.
    """
    if is_string(paths):
        paths = (paths,)
    return _fix_paths(paths,local_path, include_non_existing)


# Hooks for colored terminal output.
# See also http://www.livinglogic.de/Python/ansistyle
def terminal_has_colors():
    if sys.platform=='cygwin' and not os.environ.has_key('USE_COLOR'):
        # Avoid importing curses that causes illegal operation
        # with a message:
        #  PYTHON2 caused an invalid page fault in
        #  module CYGNURSES7.DLL as 015f:18bbfc28
        # Details: Python 2.3.3 [GCC 3.3.1 (cygming special)]
        #          ssh to Win32 machine from debian
        #          curses.version is 2.2
        #          CYGWIN_98-4.10, release 1.5.7(0.109/3/2))
        return 0
    if hasattr(sys.stdout,'isatty') and sys.stdout.isatty():
        try:
            import curses
            curses.setupterm()
            if (curses.tigetnum("colors") >= 0
                and curses.tigetnum("pairs") >= 0
                and ((curses.tigetstr("setf") is not None
                      and curses.tigetstr("setb") is not None)
                     or (curses.tigetstr("setaf") is not None
                         and curses.tigetstr("setab") is not None)
                     or curses.tigetstr("scp") is not None)):
                return 1
        except Exception,msg:
            pass
    return 0

if terminal_has_colors():
    def red_text(s): return '\x1b[31m%s\x1b[0m'%s
    def green_text(s): return '\x1b[32m%s\x1b[0m'%s
    def yellow_text(s): return '\x1b[33m%s\x1b[0m'%s
    def blue_text(s): return '\x1b[34m%s\x1b[0m'%s
    def cyan_text(s): return '\x1b[35m%s\x1b[0m'%s
else:
    def red_text(s): return s
    def green_text(s): return s
    def yellow_text(s): return s
    def cyan_text(s): return s
    def blue_text(s): return s

#########################

def cyg2win32(path):
    if sys.platform=='cygwin' and path.startswith('/cygdrive'):
        path = path[10] + ':' + os.path.normcase(path[11:])
    return path

def mingw32():
    """ Return true when using mingw32 environment.
    """
    if sys.platform=='win32':
        if os.environ.get('OSTYPE','')=='msys':
            return True
        if os.environ.get('MSYSTEM','')=='MINGW32':
            return True
    return False

def msvc_runtime_library():
    "return name of MSVC runtime library if Python was built with MSVC >= 7"
    msc_pos = sys.version.find('MSC v.')
    if msc_pos != -1:
        msc_ver = sys.version[msc_pos+6:msc_pos+10]
        lib = {'1300' : 'msvcr70',    # MSVC 7.0
               '1310' : 'msvcr71',    # MSVC 7.1
               '1400' : 'msvcr80',    # MSVC 8
              }.get(msc_ver, None)
    else:
        lib = None
    return lib

#########################

#XXX need support for .C that is also C++
cxx_ext_match = re.compile(r'.*[.](cpp|cxx|cc)\Z',re.I).match
fortran_ext_match = re.compile(r'.*[.](f90|f95|f77|for|ftn|f)\Z',re.I).match
f90_ext_match = re.compile(r'.*[.](f90|f95)\Z',re.I).match
f90_module_name_match = re.compile(r'\s*module\s*(?P<name>[\w_]+)',re.I).match
def _get_f90_modules(source):
    """ Return a list of Fortran f90 module names that
    given source file defines.
    """
    if not f90_ext_match(source):
        return []
    modules = []
    f = open(source,'r')
    f_readlines = getattr(f,'xreadlines',f.readlines)
    for line in f_readlines():
        m = f90_module_name_match(line)
        if m:
            name = m.group('name')
            modules.append(name)
            # break  # XXX can we assume that there is one module per file?
    f.close()
    return modules

def is_string(s):
    return isinstance(s, str)

def all_strings(lst):
    """ Return True if all items in lst are string objects. """
    for item in lst:
        if not is_string(item):
            return False
    return True

def is_sequence(seq):
    if is_string(seq):
        return False
    try:
        len(seq)
    except:
        return False
    return True

def is_glob_pattern(s):
    return is_string(s) and ('*' in s or '?' is s)

def as_list(seq):
    if is_sequence(seq):
        return list(seq)
    else:
        return [seq]

def has_f_sources(sources):
    """ Return True if sources contains Fortran files """
    for source in sources:
        if fortran_ext_match(source):
            return True
    return False

def has_cxx_sources(sources):
    """ Return True if sources contains C++ files """
    for source in sources:
        if cxx_ext_match(source):
            return True
    return False

def filter_sources(sources):
    """ Return four lists of filenames containing
    C, C++, Fortran, and Fortran 90 module sources,
    respectively.
    """
    c_sources = []
    cxx_sources = []
    f_sources = []
    fmodule_sources = []
    for source in sources:
        if fortran_ext_match(source):
            modules = _get_f90_modules(source)
            if modules:
                fmodule_sources.append(source)
            else:
                f_sources.append(source)
        elif cxx_ext_match(source):
            cxx_sources.append(source)
        else:
            c_sources.append(source)
    return c_sources, cxx_sources, f_sources, fmodule_sources


def _get_headers(directory_list):
    # get *.h files from list of directories
    headers = []
    for d in directory_list:
        head = glob.glob(os.path.join(d,"*.h")) #XXX: *.hpp files??
        headers.extend(head)
    return headers

def _get_directories(list_of_sources):
    # get unique directories from list of sources.
    direcs = []
    for f in list_of_sources:
        d = os.path.split(f)
        if d[0] != '' and not d[0] in direcs:
            direcs.append(d[0])
    return direcs

def get_dependencies(sources):
    #XXX scan sources for include statements
    return _get_headers(_get_directories(sources))

def is_local_src_dir(directory):
    """ Return true if directory is local directory.
    """
    if not is_string(directory):
        return False
    abs_dir = os.path.abspath(directory)
    c = os.path.commonprefix([os.getcwd(),abs_dir])
    new_dir = abs_dir[len(c):].split(os.sep)
    if new_dir and not new_dir[0]:
        new_dir = new_dir[1:]
    if new_dir and new_dir[0]=='build':
        return False
    new_dir = os.sep.join(new_dir)
    return os.path.isdir(new_dir)

def general_source_files(top_path):
    pruned_directories = {'CVS':1, '.svn':1, 'build':1}
    prune_file_pat = re.compile(r'(?:[~#]|\.py[co]|\.o)$')
    for dirpath, dirnames, filenames in os.walk(top_path, topdown=True):
        pruned = [ d for d in dirnames if d not in pruned_directories ]
        dirnames[:] = pruned
        for f in filenames:
            if not prune_file_pat.search(f):
                yield os.path.join(dirpath, f)

def general_source_directories_files(top_path):
    """ Return a directory name relative to top_path and
    files contained.
    """
    pruned_directories = ['CVS','.svn','build']
    prune_file_pat = re.compile(r'(?:[~#]|\.py[co]|\.o)$')
    for dirpath, dirnames, filenames in os.walk(top_path, topdown=True):
        pruned = [ d for d in dirnames if d not in pruned_directories ]
        dirnames[:] = pruned
        for d in dirnames:
            dpath = os.path.join(dirpath, d)
            rpath = rel_path(dpath, top_path)
            files = []
            for f in os.listdir(dpath):
                fn = os.path.join(dpath,f)
                if os.path.isfile(fn) and not prune_file_pat.search(fn):
                    files.append(fn)
            yield rpath, files
    dpath = top_path
    rpath = rel_path(dpath, top_path)
    filenames = [os.path.join(dpath,f) for f in os.listdir(dpath) \
                 if not prune_file_pat.search(f)]
    files = [f for f in filenames if os.path.isfile(f)]
    yield rpath, files


def get_ext_source_files(ext):
    # Get sources and any include files in the same directory.
    filenames = []
    sources = filter(is_string, ext.sources)
    filenames.extend(sources)
    filenames.extend(get_dependencies(sources))
    for d in ext.depends:
        if is_local_src_dir(d):
            filenames.extend(list(general_source_files(d)))
        elif os.path.isfile(d):
            filenames.append(d)
    return filenames

def get_script_files(scripts):
    scripts = filter(is_string, scripts)
    return scripts

def get_lib_source_files(lib):
    filenames = []
    sources = lib[1].get('sources',[])
    sources = filter(is_string, sources)
    filenames.extend(sources)
    filenames.extend(get_dependencies(sources))
    depends = lib[1].get('depends',[])
    for d in depends:
        if is_local_src_dir(d):
            filenames.extend(list(general_source_files(d)))
        elif os.path.isfile(d):
            filenames.append(d)
    return filenames

def get_data_files(data):
    if is_string(data):
        return [data]
    sources = data[1]
    filenames = []
    for s in sources:
        if callable(s):
            continue
        if is_local_src_dir(s):
            filenames.extend(list(general_source_files(s)))
        elif is_string(s):
            if os.path.isfile(s):
                filenames.append(s)
            else:
                print 'Not existing data file:',s
        else:
            raise TypeError,repr(s)
    return filenames

def dot_join(*args):
    return '.'.join([a for a in args if a])

def get_frame(level=0):
    """ Return frame object from call stack with given level.
    """
    try:
        return sys._getframe(level+1)
    except AttributeError:
        frame = sys.exc_info()[2].tb_frame
        for _ in range(level+1):
            frame = frame.f_back
        return frame

######################

class Configuration(object):

    _list_keys = ['packages', 'ext_modules', 'data_files', 'include_dirs',
                  'libraries', 'headers', 'scripts', 'py_modules']
    _dict_keys = ['package_dir']
    _extra_keys = ['name', 'version']

    numpy_include_dirs = []

    def __init__(self,
                 package_name=None,
                 parent_name=None,
                 top_path=None,
                 package_path=None,
                 caller_level=1,
                 **attrs):
        """ Construct configuration instance of a package.

        package_name -- name of the package
                        Ex.: 'distutils'
        parent_name  -- name of the parent package
                        Ex.: 'numpy'
        top_path     -- directory of the toplevel package
                        Ex.: the directory where the numpy package source sits
        package_path -- directory of package. Will be computed by magic from the
                        directory of the caller module if not specified
                        Ex.: the directory where numpy.distutils is
        caller_level -- frame level to caller namespace, internal parameter.
        """
        self.name = dot_join(parent_name, package_name)
        self.version = None

        caller_frame = get_frame(caller_level)
        caller_name = eval('__name__',caller_frame.f_globals,caller_frame.f_locals)
        self.local_path = get_path(caller_name, top_path)
        if top_path is None:
            top_path = self.local_path
            self.local_path = '.'
        if package_path is None:
            package_path = self.local_path
        elif os.path.isdir(njoin(self.local_path,package_path)):
            package_path = njoin(self.local_path,package_path)
        if not os.path.isdir(package_path):
            raise ValueError("%r is not a directory" % (package_path,))
        self.top_path = top_path
        self.package_path = package_path
        # this is the relative path in the installed package
        self.path_in_package = os.path.join(*self.name.split('.'))

        self.list_keys = self._list_keys[:]
        self.dict_keys = self._dict_keys[:]

        for n in self.list_keys:
            v = copy.copy(attrs.get(n, []))
            setattr(self, n, as_list(v))

        for n in self.dict_keys:
            v = copy.copy(attrs.get(n, {}))
            setattr(self, n, v)

        known_keys = self.list_keys + self.dict_keys
        self.extra_keys = self._extra_keys[:]
        for n in attrs.keys():
            if n in known_keys:
                continue
            a = attrs[n]
            setattr(self,n,a)
            if isinstance(a, list):
                self.list_keys.append(n)
            elif isinstance(a, dict):
                self.dict_keys.append(n)
            else:
                self.extra_keys.append(n)

        if os.path.exists(njoin(package_path,'__init__.py')):
            self.packages.append(self.name)
            self.package_dir[self.name] = package_path

        self.options = dict(
            ignore_setup_xxx_py = False,
            assume_default_configuration = False,
            delegate_options_to_subpackages = False,
            quiet = False,
            )

        caller_instance = None
        for i in range(1,3):
            try:
                f = get_frame(i)
            except ValueError:
                break
            try:
                caller_instance = eval('self',f.f_globals,f.f_locals)
                break
            except NameError:
                pass
        if isinstance(caller_instance, self.__class__):
            if caller_instance.options['delegate_options_to_subpackages']:
                self.set_options(**caller_instance.options)

    def todict(self):
        """ Return configuration distionary suitable for passing
        to distutils.core.setup() function.
        """
        self._optimize_data_files()
        d = {}
        known_keys = self.list_keys + self.dict_keys + self.extra_keys
        for n in known_keys:
            a = getattr(self,n)
            if a:
                d[n] = a
        return d

    def info(self, message):
        if not self.options['quiet']:
            print message

    def warn(self, message):
        print>>sys.stderr, blue_text('Warning: %s' % (message,))

    def set_options(self, **options):
        """ Configure Configuration instance.

        The following options are available:
        - ignore_setup_xxx_py
        - assume_default_configuration
        - delegate_options_to_subpackages
        - quiet
        """
        for key, value in options.items():
            if self.options.has_key(key):
                self.options[key] = value
            else:
                raise ValueError,'Unknown option: '+key

    def get_distribution(self):
        from numpy.distutils.core import get_distribution
        return get_distribution()

    def _wildcard_get_subpackage(self, subpackage_name,
                                 parent_name,
                                 caller_level = 1):
        l = subpackage_name.split('.')
        subpackage_path = njoin([self.local_path]+l)
        dirs = filter(os.path.isdir,glob.glob(subpackage_path))
        config_list = []
        for d in dirs:
            if not os.path.isfile(njoin(d,'__init__.py')):
                continue
            if 'build' in d.split(os.sep):
                continue
            n = '.'.join(d.split(os.sep)[-len(l):])
            c = self.get_subpackage(n,
                                    parent_name = parent_name,
                                    caller_level = caller_level+1)
            config_list.extend(c)
        return config_list

    def _get_configuration_from_setup_py(self, setup_py,
                                         subpackage_name,
                                         subpackage_path,
                                         parent_name,
                                         caller_level = 1):
        # In case setup_py imports local modules:
        sys.path.insert(0,os.path.dirname(setup_py))
        try:
            fo_setup_py = open(setup_py, 'U')
            setup_name = os.path.splitext(os.path.basename(setup_py))[0]
            n = dot_join(self.name,subpackage_name,setup_name)
            setup_module = imp.load_module('_'.join(n.split('.')),
                                           fo_setup_py,
                                           setup_py,
                                           ('.py', 'U', 1))
            fo_setup_py.close()
            if not hasattr(setup_module,'configuration'):
                if not self.options['assume_default_configuration']:
                    self.warn('Assuming default configuration '\
                              '(%s does not define configuration())'\
                              % (setup_module))
                config = Configuration(subpackage_name, parent_name,
                                       self.top_path, subpackage_path,
                                       caller_level = caller_level + 1)
            else:
                pn = dot_join(*([parent_name] + subpackage_name.split('.')[:-1]))
                args = (pn,)
                if setup_module.configuration.func_code.co_argcount > 1:
                    args = args + (self.top_path,)
                config = setup_module.configuration(*args)
            if config.name!=dot_join(parent_name,subpackage_name):
                self.warn('Subpackage %r configuration returned as %r' % \
                          (dot_join(parent_name,subpackage_name), config.name))
        finally:
            del sys.path[0]
        return config

    def get_subpackage(self,subpackage_name,
                       subpackage_path=None,
                       parent_name=None,
                       caller_level = 1):
        """ Return list of subpackage configurations.

        '*' in subpackage_name is handled as a wildcard.
        """
        if subpackage_name is None:
            if subpackage_path is None:
                raise ValueError(
                    "either subpackage_name or subpackage_path must be specified")
            subpackage_name = os.path.basename(subpackage_path)

        # handle wildcards
        l = subpackage_name.split('.')
        if subpackage_path is None and '*' in subpackage_name:
            return self._wildcard_get_subpackage(subpackage_name,
                                                 parent_name,
                                                 caller_level = caller_level+1)
        assert '*' not in subpackage_name,`subpackage_name, subpackage_path,parent_name`
        if subpackage_path is None:
            subpackage_path = njoin([self.local_path] + l)
        else:
            subpackage_path = njoin([subpackage_path] + l[:-1])
            subpackage_path = self.paths([subpackage_path])[0]
        setup_py = njoin(subpackage_path, 'setup.py')
        if not self.options['ignore_setup_xxx_py']:
            if not os.path.isfile(setup_py):
                setup_py = njoin(subpackage_path,
                                 'setup_%s.py' % (subpackage_name))
        if not os.path.isfile(setup_py):
            if not self.options['assume_default_configuration']:
                self.warn('Assuming default configuration '\
                          '(%s/{setup_%s,setup}.py was not found)' \
                          % (os.path.dirname(setup_py), subpackage_name))
            config = Configuration(subpackage_name, parent_name,
                                   self.top_path, subpackage_path,
                                   caller_level = caller_level+1)
        else:
            config = self._get_configuration_from_setup_py(
                setup_py,
                subpackage_name,
                subpackage_path,
                parent_name,
                caller_level = caller_level + 1)
        if config:
            return [config]
        else:
            return []

    def add_subpackage(self,subpackage_name,
                       subpackage_path=None,
                       standalone = False):
        """ Add subpackage to configuration.
        """
        if standalone:
            parent_name = None
        else:
            parent_name = self.name
        config_list = self.get_subpackage(subpackage_name,subpackage_path,
                                          parent_name = parent_name,
                                          caller_level = 2)
        if not config_list:
            self.warn('No configuration returned, assuming unavailable.')
        for config in config_list:
            d = config
            if isinstance(config, Configuration):
                d = config.todict()
            assert isinstance(d,dict),`type(d)`

            self.info('Appending %s configuration to %s' \
                      % (d.get('name'), self.name))
            self.dict_append(**d)

        dist = self.get_distribution()
        if dist is not None:
            self.warn('distutils distribution has been initialized,'\
                      ' it may be too late to add a subpackage '+ subpackage_name)
        return

    def add_data_dir(self,data_path):
        """ Recursively add files under data_path to data_files list.
        Argument can be either
        - 2-sequence (<datadir suffix>,<path to data directory>)
        - path to data directory where python datadir suffix defaults
          to package dir.

        Rules for installation paths:
          foo/bar -> (foo/bar, foo/bar) -> parent/foo/bar
          (gun, foo/bar) -> parent/gun
          foo/* -> (foo/a, foo/a), (foo/b, foo/b) -> parent/foo/a, parent/foo/b
          (gun, foo/*) -> (gun, foo/a), (gun, foo/b) -> gun
          (gun/*, foo/*) -> parent/gun/a, parent/gun/b
          /foo/bar -> (bar, /foo/bar) -> parent/bar
          (gun, /foo/bar) -> parent/gun
          (fun/*/gun/*, sun/foo/bar) -> parent/fun/foo/gun/bar
        """
        if is_sequence(data_path):
            d, data_path = data_path
        else:
            d = None
        if is_sequence(data_path):
            [self.add_data_dir((d,p)) for p in data_path]
            return
        if not is_string(data_path):
            raise TypeError("not a string: %r" % (data_path,))
        if d is None:
            if os.path.isabs(data_path):
                return self.add_data_dir((os.path.basename(data_path), data_path))
            return self.add_data_dir((data_path, data_path))
        paths = self.paths(data_path, include_non_existing=False)
        if is_glob_pattern(data_path):
            if is_glob_pattern(d):
                pattern_list = allpath(d).split(os.sep)
                pattern_list.reverse()
                # /a/*//b/ -> /a/*/b
                rl = range(len(pattern_list)-1); rl.reverse()
                for i in rl:
                    if not pattern_list[i]:
                        del pattern_list[i]
                #
                for path in paths:
                    if not os.path.isdir(path):
                        print 'Not a directory, skipping',path
                        continue
                    rpath = rel_path(path, self.local_path)
                    path_list = rpath.split(os.sep)
                    path_list.reverse()
                    target_list = []
                    i = 0
                    for s in pattern_list:
                        if is_glob_pattern(s):
                            if i>=len(path_list):
                                raise ValueError,'cannot fill pattern %r with %r' \
                                      % (d, path)
                            target_list.append(path_list[i])
                        else:
                            assert s==path_list[i],`s,path_list[i],data_path,d,path,rpath`
                            target_list.append(s)
                        i += 1
                    if path_list[i:]:
                        self.warn('mismatch of pattern_list=%s and path_list=%s'\
                                  % (pattern_list,path_list))
                    target_list.reverse()
                    self.add_data_dir((os.sep.join(target_list),path))
            else:
                for path in paths:
                    self.add_data_dir((d,path))
            return
        assert not is_glob_pattern(d),`d`

        dist = self.get_distribution()
        if dist is not None:
            data_files = dist.data_files
        else:
            data_files = self.data_files

        for path in paths:
            for d1,f in list(general_source_directories_files(path)):
                target_path = os.path.join(self.path_in_package,d,d1)
                data_files.append((target_path, f))
        return

    def _optimize_data_files(self):
        data_dict = {}
        for p,files in self.data_files:
            if not data_dict.has_key(p):
                data_dict[p] = set()
            map(data_dict[p].add,files)
        self.data_files[:] = [(p,list(files)) for p,files in data_dict.items()]
        return

    def add_data_files(self,*files):
        """ Add data files to configuration data_files.
        Argument(s) can be either
        - 2-sequence (<datadir prefix>,<path to data file(s)>)
        - paths to data files where python datadir prefix defaults
          to package dir.

        Rules for installation paths:
          file.txt -> (., file.txt)-> parent/file.txt
          foo/file.txt -> (foo, foo/file.txt) -> parent/foo/file.txt
          /foo/bar/file.txt -> (., /foo/bar/file.txt) -> parent/file.txt
          *.txt -> parent/a.txt, parent/b.txt
          foo/*.txt -> parent/foo/a.txt, parent/foo/b.txt
          */*.txt -> (*, */*.txt) -> parent/c/a.txt, parent/d/b.txt
          (sun, file.txt) -> parent/sun/file.txt
          (sun, bar/file.txt) -> parent/sun/file.txt
          (sun, /foo/bar/file.txt) -> parent/sun/file.txt
          (sun, *.txt) -> parent/sun/a.txt, parent/sun/b.txt
          (sun, bar/*.txt) -> parent/sun/a.txt, parent/sun/b.txt
          (sun/*, */*.txt) -> parent/sun/c/a.txt, parent/d/b.txt
        """

        if len(files)>1:
            map(self.add_data_files, files)
            return
        assert len(files)==1
        if is_sequence(files[0]):
            d,files = files[0]
        else:
            d = None
        if is_string(files):
            filepat = files
        elif is_sequence(files):
            if len(files)==1:
                filepat = files[0]
            else:
                for f in files:
                    self.add_data_files((d,f))
                return
        else:
            raise TypeError,`type(files)`

        if d is None:
            if callable(filepat):
                d = ''
            elif os.path.isabs(filepat):
                d = ''
            else:
                d = os.path.dirname(filepat)
            self.add_data_files((d,files))
            return

        paths = self.paths(filepat, include_non_existing=False)
        if is_glob_pattern(filepat):
            if is_glob_pattern(d):
                pattern_list = d.split(os.sep)
                pattern_list.reverse()
                for path in paths:
                    path_list = path.split(os.sep)
                    path_list.reverse()
                    path_list.pop() # filename
                    target_list = []
                    i = 0
                    for s in pattern_list:
                        if is_glob_pattern(s):
                            target_list.append(path_list[i])
                            i += 1
                        else:
                            target_list.append(s)
                    target_list.reverse()
                    self.add_data_files((os.sep.join(target_list), path))
            else:
                self.add_data_files((d,paths))
            return
        assert not is_glob_pattern(d),`d,filepat`

        dist = self.get_distribution()
        if dist is not None:
            data_files = dist.data_files
        else:
            data_files = self.data_files

        data_files.append((os.path.join(self.path_in_package,d),paths))
        return

    ### XXX Implement add_py_modules

    def add_include_dirs(self,*paths):
        """ Add paths to configuration include directories.
        """
        include_dirs = self.paths(paths)
        dist = self.get_distribution()
        if dist is not None:
            dist.include_dirs.extend(include_dirs)
        else:
            self.include_dirs.extend(include_dirs)
        return

    def add_numarray_include_dirs(self):
	import numpy.numarray.util as nnu
	self.add_include_dirs(*nnu.get_numarray_include_dirs())
	
    def add_headers(self,*files):
        """ Add installable headers to configuration.
        Argument(s) can be either
        - 2-sequence (<includedir suffix>,<path to header file(s)>)
        - path(s) to header file(s) where python includedir suffix will default
          to package name.
        """
        headers = []
        for path in files:
            if is_string(path):
                [headers.append((self.name,p)) for p in self.paths(path)]
            else:
                if not isinstance(path, (tuple, list)) or len(path) != 2:
                    raise TypeError(repr(path))
                [headers.append((path[0],p)) for p in self.paths(path[1])]
        dist = self.get_distribution()
        if dist is not None:
            dist.headers.extend(headers)
        else:
            self.headers.extend(headers)
        return

    def paths(self,*paths,**kws):
        """ Apply glob to paths and prepend local_path if needed.
        """
        include_non_existing = kws.get('include_non_existing',True)
        return gpaths(paths,
                      local_path = self.local_path,
                      include_non_existing=include_non_existing)

    def _fix_paths_dict(self,kw):
        for k in kw.keys():
            v = kw[k]
            if k in ['sources','depends','include_dirs','library_dirs',
                     'module_dirs','extra_objects']:
                new_v = self.paths(v)
                kw[k] = new_v
        return

    def add_extension(self,name,sources,**kw):
        """ Add extension to configuration.

        Keywords:
          include_dirs, define_macros, undef_macros,
          library_dirs, libraries, runtime_library_dirs,
          extra_objects, extra_compile_args, extra_link_args,
          export_symbols, swig_opts, depends, language,
          f2py_options, module_dirs
          extra_info - dict or list of dict of keywords to be
                       appended to keywords.
        """
        ext_args = copy.copy(kw)
        ext_args['name'] = dot_join(self.name,name)
        ext_args['sources'] = sources

        if ext_args.has_key('extra_info'):
            extra_info = ext_args['extra_info']
            del ext_args['extra_info']
            if isinstance(extra_info, dict):
                extra_info = [extra_info]
            for info in extra_info:
                assert isinstance(info, dict), repr(info)
                dict_append(ext_args,**info)

        self._fix_paths_dict(ext_args)

        # Resolve out-of-tree dependencies
        libraries = ext_args.get('libraries',[])
        libnames = []
        ext_args['libraries'] = []
        for libname in libraries:
            if isinstance(libname,tuple):
                self._fix_paths_dict(libname[1])

            # Handle library names of the form libname@relative/path/to/library
            if '@' in libname:
                lname,lpath = libname.split('@',1)
                lpath = os.path.abspath(njoin(self.local_path,lpath))
                if os.path.isdir(lpath):
                    c = self.get_subpackage(None,lpath,
                                            caller_level = 2)
                    if isinstance(c,Configuration):
                        c = c.todict()
                    for l in [l[0] for l in c.get('libraries',[])]:
                        llname = l.split('__OF__',1)[0]
                        if llname == lname:
                            c.pop('name',None)
                            dict_append(ext_args,**c)
                            break
                    continue
            libnames.append(libname)

        ext_args['libraries'] = libnames + ext_args['libraries']

        from numpy.distutils.core import Extension
        ext = Extension(**ext_args)
        self.ext_modules.append(ext)

        dist = self.get_distribution()
        if dist is not None:
            self.warn('distutils distribution has been initialized,'\
                      ' it may be too late to add an extension '+name)
        return ext

    def add_library(self,name,sources,**build_info):
        """ Add library to configuration.

        Valid keywords for build_info:
          depends
          macros
          include_dirs
          extra_compiler_args
          f2py_options
        """
        build_info = copy.copy(build_info)
        name = name #+ '__OF__' + self.name
        build_info['sources'] = sources

        self._fix_paths_dict(build_info)

        self.libraries.append((name,build_info))

        dist = self.get_distribution()
        if dist is not None:
            self.warn('distutils distribution has been initialized,'\
                      ' it may be too late to add a library '+ name)
        return

    def add_scripts(self,*files):
        """ Add scripts to configuration.
        """
        scripts = self.paths(files)
        dist = self.get_distribution()
        if dist is not None:
            dist.scripts.extend(scripts)
        else:
            self.scripts.extend(scripts)
        return

    def dict_append(self,**dict):
        for key in self.list_keys:
            a = getattr(self,key)
            a.extend(dict.get(key,[]))
        for key in self.dict_keys:
            a = getattr(self,key)
            a.update(dict.get(key,{}))
        known_keys = self.list_keys + self.dict_keys + self.extra_keys
        for key in dict.keys():
            if key not in known_keys:
                a = getattr(self, key, None)
                if a and a==dict[key]: continue
                self.warn('Inheriting attribute %r=%r from %r' \
                          % (key,dict[key],dict.get('name','?')))
                setattr(self,key,dict[key])
                self.extra_keys.append(key)
            elif key in self.extra_keys:
                self.info('Ignoring attempt to set %r (from %r to %r)' \
                          % (key, getattr(self,key), dict[key]))
            elif key in known_keys:
                # key is already processed above
                pass
            else:
                raise ValueError, "Don't know about key=%r" % (key)
        return

    def __str__(self):
        from pprint import pformat
        known_keys = self.list_keys + self.dict_keys + self.extra_keys
        s = '<'+5*'-' + '\n'
        s += 'Configuration of '+self.name+':\n'
        known_keys.sort()
        for k in known_keys:
            a = getattr(self,k,None)
            if a:
                s += '%s = %s\n' % (k,pformat(a))
        s += 5*'-' + '>'
        return s

    def get_config_cmd(self):
        cmd = get_cmd('config')
        cmd.ensure_finalized()
        cmd.dump_source = 0
        cmd.noisy = 0
        old_path = os.environ.get('PATH')
        if old_path:
            path = os.pathsep.join(['.',old_path])
            os.environ['PATH'] = path
        return cmd

    def get_build_temp_dir(self):
        cmd = get_cmd('build')
        cmd.ensure_finalized()
        return cmd.build_temp

    def have_f77c(self):
        """ Check for availability of Fortran 77 compiler.
        Use it inside source generating function to ensure that
        setup distribution instance has been initialized.
        """
        simple_fortran_subroutine = '''
        subroutine simple
        end
        '''
        config_cmd = self.get_config_cmd()
        flag = config_cmd.try_compile(simple_fortran_subroutine,lang='f77')
        return flag

    def have_f90c(self):
        """ Check for availability of Fortran 90 compiler.
        Use it inside source generating function to ensure that
        setup distribution instance has been initialized.
        """
        simple_fortran_subroutine = '''
        subroutine simple
        end
        '''
        config_cmd = self.get_config_cmd()
        flag = config_cmd.try_compile(simple_fortran_subroutine,lang='f90')
        return flag

    def append_to(self, extlib):
        """ Append libraries, include_dirs to extension or library item.
        """
        if is_sequence(extlib):
            lib_name, build_info = extlib
            dict_append(build_info,
                        libraries=self.libraries,
                        include_dirs=self.include_dirs)
        else:
            from numpy.distutils.core import Extension
            assert isinstance(extlib,Extension), repr(extlib)
            extlib.libraries.extend(self.libraries)
            extlib.include_dirs.extend(self.include_dirs)
        return

    def _get_svn_revision(self,path):
        """ Return path's SVN revision number.
        """
        entries = njoin(path,'.svn','entries')
        revision = None
        if os.path.isfile(entries):
            f = open(entries)
            m = re.search(r'revision="(?P<revision>\d+)"',f.read())
            f.close()
            if m:
                revision = int(m.group('revision'))
        return revision

    def get_version(self, version_file=None, version_variable=None):
        """ Try to get version string of a package.
        """
        version = getattr(self,'version',None)
        if version is not None:
            return version

        # Get version from version file.
        if version_file is None:
            files = ['__version__.py',
                     self.name.split('.')[-1]+'_version.py',
                     'version.py',
                     '__svn_version__.py']
        else:
            files = [version_file]
        if version_variable is None:
            version_vars = ['version',
                            '__version__',
                            self.name.split('.')[-1]+'_version']
        else:
            version_vars = [version_variable]
        for f in files:
            fn = njoin(self.local_path,f)
            if os.path.isfile(fn):
                info = (open(fn),fn,('.py','U',1))
                name = os.path.splitext(os.path.basename(fn))[0]
                n = dot_join(self.name,name)
                try:
                    version_module = imp.load_module('_'.join(n.split('.')),*info)
                except ImportError,msg:
                    self.warn(str(msg))
                    version_module = None
                if version_module is None:
                    continue

                for a in version_vars:
                    version = getattr(version_module,a,None)
                    if version is not None:
                        break
                if version is not None:
                    break

        if version is not None:
            self.version = version
            return version

        # Get version as SVN revision number
        revision = self._get_svn_revision(self.local_path)
        if revision is not None:
            version = str(revision)
            self.version = version

        return version

    def make_svn_version_py(self):
        """ Generate package __svn_version__.py file from SVN revision number,
        it will be removed after python exits but will be available
        when sdist, etc commands are executed.

        If __svn_version__.py existed before, nothing is done.
        """
        target = njoin(self.local_path,'__svn_version__.py')
        if os.path.isfile(target):
            return
        def generate_svn_version_py():
            if not os.path.isfile(target):
                revision = self._get_svn_revision(self.local_path)
                assert revision is not None,'hmm, why I am not inside SVN tree???'
                version = str(revision)
                self.info('Creating %s (version=%r)' % (target,version))
                f = open(target,'w')
                f.write('version = %r\n' % (version))
                f.close()

            import atexit
            def rm_file(f=target,p=self.info):
                try: os.remove(f); p('removed '+f)
                except OSError: pass
                try: os.remove(f+'c'); p('removed '+f+'c')
                except OSError: pass
            atexit.register(rm_file)

            return target

        self.add_data_files(('', generate_svn_version_py()))

    def make_config_py(self,name='__config__'):
        """ Generate package __config__.py file containing system_info
        information used during building the package.
        """
        self.py_modules.append((self.name,name,generate_config_py))
        return

    def get_info(self,*names):
        """ Get resources information.
        """
        from system_info import get_info, dict_append
        info_dict = {}
        for a in names:
            dict_append(info_dict,**get_info(a))
        return info_dict


def get_cmd(cmdname, _cache={}):
    if not _cache.has_key(cmdname):
        import distutils.core
        dist = distutils.core._setup_distribution
        if dist is None:
            from distutils.errors import DistutilsInternalError
            raise DistutilsInternalError(
                  'setup distribution instance not initialized')
        cmd = dist.get_command_obj(cmdname)
        _cache[cmdname] = cmd
    return _cache[cmdname]

def get_numpy_include_dirs():
    # numpy_include_dirs are set by numpy/core/setup.py, otherwise []
    include_dirs = Configuration.numpy_include_dirs[:]
    if not include_dirs:
        import numpy
        if numpy.show_config is None:
            # running from numpy_core source directory
            include_dirs.append(njoin(os.path.dirname(numpy.__file__),
                                             'core', 'include'))
        else:
            # using installed numpy core headers
            import numpy.core as core
            include_dirs.append(njoin(os.path.dirname(core.__file__), 'include'))
    # else running numpy/core/setup.py
    return include_dirs

#########################

def default_config_dict(name = None, parent_name = None, local_path=None):
    """ Return a configuration dictionary for usage in
    configuration() function defined in file setup_<name>.py.
    """
    import warnings
    warnings.warn('Use Configuration(%r,%r,top_path=%r) instead of '\
                  'deprecated default_config_dict(%r,%r,%r)'
                  % (name, parent_name, local_path,
                     name, parent_name, local_path,
                     ))
    c = Configuration(name, parent_name, local_path)
    return c.todict()


def dict_append(d, **kws):
    for k, v in kws.items():
        if d.has_key(k):
            d[k].extend(v)
        else:
            d[k] = v

def appendpath(prefix, path):
    if os.path.sep != '/':
        prefix = prefix.replace('/', os.path.sep)
        path = path.replace('/', os.path.sep)
    drive = ''
    if os.path.isabs(path):
        drive = os.path.splitdrive(prefix)[0]
        absprefix = os.path.splitdrive(os.path.abspath(prefix))[1]
        pathdrive, path = os.path.splitdrive(path)
        d = os.path.commonprefix([absprefix, path])
        if os.path.join(absprefix[:len(d)], absprefix[len(d):]) != absprefix \
           or os.path.join(path[:len(d)], path[len(d):]) != path:
            # Handle invalid paths
            d = os.path.dirname(d)
        subpath = path[len(d):]
        if os.path.isabs(subpath):
            subpath = subpath[1:]
    else:
        subpath = path
    return os.path.normpath(njoin(drive + prefix, subpath))

def generate_config_py(target):
    """ Generate config.py file containing system_info information
    used during building the package.

    Usage:\
        config['py_modules'].append((packagename, '__config__',generate_config_py))
    """
    from numpy.distutils.system_info import system_info
    from distutils.dir_util import mkpath
    mkpath(os.path.dirname(target))
    f = open(target, 'w')
    f.write('# This file is generated by %s\n' % (os.path.abspath(sys.argv[0])))
    f.write('# It contains system_info results at the time of building this package.\n')
    f.write('__all__ = ["get_info","show"]\n\n')
    for k, i in system_info.saved_results.items():
        f.write('%s=%r\n' % (k, i))
    f.write('\ndef get_info(name):\n    g=globals()\n    return g.get(name,g.get(name+"_info",{}))\n')
    f.write('''
def show():
    for name,info_dict in globals().items():
        if name[0]=="_" or type(info_dict) is not type({}): continue
        print name+":"
        if not info_dict:
            print "  NOT AVAILABLE"
        for k,v in info_dict.items():
            v = str(v)
            if k==\'sources\' and len(v)>200: v = v[:60]+\' ...\\n... \'+v[-60:]
            print \'    %s = %s\'%(k,v)
        print
    return
    ''')

    f.close()
    return target

# Colored log, requires Python 2.3 or up.

import sys
from distutils.log import *
from distutils.log import Log as old_Log
from distutils.log import _global_log
from misc_util import red_text, yellow_text, cyan_text, is_sequence, is_string


def _fix_args(args,flag=1):
    if is_string(args):
        return args.replace('%','%%')
    if flag and is_sequence(args):
        return tuple([_fix_args(a,flag=0) for a in args])
    return args

class Log(old_Log):
    def _log(self, level, msg, args):
        if level >= self.threshold:
            if args:
                print _global_color_map[level](msg % _fix_args(args))
            else:
                print _global_color_map[level](msg)
            sys.stdout.flush()
_global_log.__class__ = Log

def set_verbosity(v):
    prev_level = _global_log.threshold
    if v < 0:
        set_threshold(ERROR)
    elif v == 0:
        set_threshold(WARN)
    elif v == 1:
        set_threshold(INFO)
    elif v >= 2:
        set_threshold(DEBUG)
    return {FATAL:-2,ERROR:-1,WARN:0,INFO:1,DEBUG:2}.get(prev_level,1)

_global_color_map = {
    DEBUG:cyan_text,
    INFO:yellow_text,
    WARN:red_text,
    ERROR:red_text,
    FATAL:red_text
}

set_verbosity(1)

""" Functions for converting from DOS to UNIX line endings
"""

import sys, re, os

def dos2unix(file):
    "Replace CRLF with LF in argument files.  Print names of changed files."
    if os.path.isdir(file):
        print file, "Directory!"
        return

    data = open(file, "rb").read()
    if '\0' in data:
        print file, "Binary!"
        return

    newdata = re.sub("\r\n", "\n", data)
    if newdata != data:
        print 'dos2unix:', file
        f = open(file, "wb")
        f.write(newdata)
        f.close()
        return file
    else:
        print file, 'ok'

def dos2unix_one_dir(modified_files,dir_name,file_names):
    for file in file_names:
        full_path = os.path.join(dir_name,file)
        file = dos2unix(full_path)
        if file is not None:
            modified_files.append(file)

def dos2unix_dir(dir_name):
    modified_files = []
    os.path.walk(dir_name,dos2unix_one_dir,modified_files)
    return modified_files
#----------------------------------

def unix2dos(file):
    "Replace LF with CRLF in argument files.  Print names of changed files."
    if os.path.isdir(file):
        print file, "Directory!"
        return

    data = open(file, "rb").read()
    if '\0' in data:
        print file, "Binary!"
        return
    newdata = re.sub("\r\n", "\n", data)
    newdata = re.sub("\n", "\r\n", newdata)
    if newdata != data:
        print 'unix2dos:', file
        f = open(file, "wb")
        f.write(newdata)
        f.close()
        return file
    else:
        print file, 'ok'

def unix2dos_one_dir(modified_files,dir_name,file_names):
    for file in file_names:
        full_path = os.path.join(dir_name,file)
        unix2dos(full_path)
        if file is not None:
            modified_files.append(file)

def unix2dos_dir(dir_name):
    modified_files = []
    os.path.walk(dir_name,unix2dos_one_dir,modified_files)
    return modified_files

if __name__ == "__main__":
    import sys
    dos2unix_dir(sys.argv[1])

import re
import sys
import os
import string

__doc__ = """This module generates a DEF file from the symbols in
an MSVC-compiled DLL import library.  It correctly discriminates between
data and functions.  The data is collected from the output of the program
nm(1).

Usage:
    python lib2def.py [libname.lib] [output.def]
or
    python lib2def.py [libname.lib] > output.def

libname.lib defaults to python<py_ver>.lib and output.def defaults to stdout

Author: Robert Kern <kernr@mail.ncifcrf.gov>
Last Update: April 30, 1999
"""

__version__ = '0.1a'

import sys

py_ver = "%d%d" % tuple(sys.version_info[:2])

DEFAULT_NM = 'nm -Cs'

DEF_HEADER = """LIBRARY         python%s.dll
;CODE           PRELOAD MOVEABLE DISCARDABLE
;DATA           PRELOAD SINGLE

EXPORTS
""" % py_ver
# the header of the DEF file

FUNC_RE = re.compile(r"^(.*) in python%s\.dll" % py_ver, re.MULTILINE)
DATA_RE = re.compile(r"^_imp__(.*) in python%s\.dll" % py_ver, re.MULTILINE)

def parse_cmd():
    """Parses the command-line arguments.

libfile, deffile = parse_cmd()"""
    if len(sys.argv) == 3:
        if sys.argv[1][-4:] == '.lib' and sys.argv[2][-4:] == '.def':
            libfile, deffile = sys.argv[1:]
        elif sys.argv[1][-4:] == '.def' and sys.argv[2][-4:] == '.lib':
            deffile, libfile = sys.argv[1:]
        else:
            print "I'm assuming that your first argument is the library"
            print "and the second is the DEF file."
    elif len(sys.argv) == 2:
        if sys.argv[1][-4:] == '.def':
            deffile = sys.argv[1]
            libfile = 'python%s.lib' % py_ver
        elif sys.argv[1][-4:] == '.lib':
            deffile = None
            libfile = sys.argv[1]
    else:
        libfile = 'python%s.lib' % py_ver
        deffile = None
    return libfile, deffile

def getnm(nm_cmd = 'nm -Cs python%s.lib' % py_ver):
    """Returns the output of nm_cmd via a pipe.

nm_output = getnam(nm_cmd = 'nm -Cs py_lib')"""
    f = os.popen(nm_cmd)
    nm_output = f.read()
    f.close()
    return nm_output

def parse_nm(nm_output):
    """Returns a tuple of lists: dlist for the list of data
symbols and flist for the list of function symbols.

dlist, flist = parse_nm(nm_output)"""
    data = DATA_RE.findall(nm_output)
    func = FUNC_RE.findall(nm_output)

    flist = []
    for sym in data:
        if sym in func and (sym[:2] == 'Py' or sym[:3] == '_Py' or sym[:4] == 'init'):
            flist.append(sym)

    dlist = []
    for sym in data:
        if sym not in flist and (sym[:2] == 'Py' or sym[:3] == '_Py'):
            dlist.append(sym)

    dlist.sort()
    flist.sort()
    return dlist, flist

def output_def(dlist, flist, header, file = sys.stdout):
    """Outputs the final DEF file to a file defaulting to stdout.

output_def(dlist, flist, header, file = sys.stdout)"""
    for data_sym in dlist:
        header = header + '\t%s DATA\n' % data_sym
    header = header + '\n' # blank line
    for func_sym in flist:
        header = header + '\t%s\n' % func_sym
    file.write(header)

if __name__ == '__main__':
    libfile, deffile = parse_cmd()
    if deffile is None:
        deffile = sys.stdout
    else:
        deffile = open(deffile, 'w')
    nm_cmd = '%s %s' % (DEFAULT_NM, libfile)
    nm_output = getnm(nm_cmd)
    dlist, flist = parse_nm(nm_output)
    output_def(dlist, flist, DEF_HEADER, deffile)

#!/bin/env python
"""
This file defines a set of system_info classes for getting
information about various resources (libraries, library directories,
include directories, etc.) in the system. Currently, the following
classes are available:

  atlas_info
  atlas_threads_info
  atlas_blas_info
  atlas_blas_threads_info
  lapack_atlas_info
  blas_info
  lapack_info
  blas_opt_info       # usage recommended
  lapack_opt_info     # usage recommended
  fftw_info,dfftw_info,sfftw_info
  fftw_threads_info,dfftw_threads_info,sfftw_threads_info
  djbfft_info
  x11_info
  lapack_src_info
  blas_src_info
  numpy_info
  numarray_info
  numpy_info
  boost_python_info
  agg2_info
  wx_info
  gdk_pixbuf_xlib_2_info
  gdk_pixbuf_2_info
  gdk_x11_2_info
  gtkp_x11_2_info
  gtkp_2_info
  xft_info
  freetype2_info
  umfpack_info

Usage:
    info_dict = get_info(<name>)
  where <name> is a string 'atlas','x11','fftw','lapack','blas',
  'lapack_src', 'blas_src', etc. For a complete list of allowed names,
  see the definition of get_info() function below.

  Returned info_dict is a dictionary which is compatible with
  distutils.setup keyword arguments. If info_dict == {}, then the
  asked resource is not available (system_info could not find it).

  Several *_info classes specify an environment variable to specify
  the locations of software. When setting the corresponding environment
  variable to 'None' then the software will be ignored, even when it
  is available in system.

Global parameters:
  system_info.search_static_first - search static libraries (.a)
             in precedence to shared ones (.so, .sl) if enabled.
  system_info.verbosity - output the results to stdout if enabled.

The file 'site.cfg' is looked for in

1) Directory of main setup.py file being run.
2) Home directory of user running the setup.py file (Not implemented yet)
3) System wide directory (location of this file...)

The first one found is used to get system configuration options The
format is that used by ConfigParser (i.e., Windows .INI style). The
section DEFAULT has options that are the default for each section. The
available sections are fftw, atlas, and x11. Appropiate defaults are
used if nothing is specified.

The order of finding the locations of resources is the following:
 1. environment variable
 2. section in site.cfg
 3. DEFAULT section in site.cfg
Only the first complete match is returned.

Example:
----------
[DEFAULT]
library_dirs = /usr/lib:/usr/local/lib:/opt/lib
include_dirs = /usr/include:/usr/local/include:/opt/include
src_dirs = /usr/local/src:/opt/src
# search static libraries (.a) in preference to shared ones (.so)
search_static_first = 0

[fftw]
fftw_libs = rfftw, fftw
fftw_opt_libs = rfftw_threaded, fftw_threaded
# if the above aren't found, look for {s,d}fftw_libs and {s,d}fftw_opt_libs

[atlas]
library_dirs = /usr/lib/3dnow:/usr/lib/3dnow/atlas
# for overriding the names of the atlas libraries
atlas_libs = lapack, f77blas, cblas, atlas

[x11]
library_dirs = /usr/X11R6/lib
include_dirs = /usr/X11R6/include
----------

Authors:
  Pearu Peterson <pearu@cens.ioc.ee>, February 2002
  David M. Cooke <cookedm@physics.mcmaster.ca>, April 2002

Copyright 2002 Pearu Peterson all rights reserved,
Pearu Peterson <pearu@cens.ioc.ee>
Permission to use, modify, and distribute this software is given under the
terms of the SciPy (BSD style) license.  See LICENSE.txt that came with
this distribution for specifics.

NO WARRANTY IS EXPRESSED OR IMPLIED.  USE AT YOUR OWN RISK.
"""

import sys
import os
import re
import copy
import warnings
from glob import glob
import ConfigParser

from distutils.errors import DistutilsError
from distutils.dist import Distribution
import distutils.sysconfig
from distutils import log

from numpy.distutils.exec_command import \
    find_executable, exec_command, get_pythonexe
from numpy.distutils.misc_util import is_sequence, is_string
from numpy.distutils.command.config import config as cmd_config

if sys.platform == 'win32':
    default_lib_dirs = ['C:\\',
                        os.path.join(distutils.sysconfig.EXEC_PREFIX,
                                     'libs')]
    default_include_dirs = []
    default_src_dirs = ['.']
    default_x11_lib_dirs = []
    default_x11_include_dirs = []
else:
    default_lib_dirs = ['/usr/local/lib', '/opt/lib', '/usr/lib',
                        '/opt/local/lib', '/sw/lib']
    default_include_dirs = ['/usr/local/include',
                            '/opt/include', '/usr/include',
                            '/opt/local/include', '/sw/include']
    default_src_dirs = ['.','/usr/local/src', '/opt/src','/sw/src']
    default_x11_lib_dirs = ['/usr/X11R6/lib','/usr/X11/lib','/usr/lib']
    default_x11_include_dirs = ['/usr/X11R6/include','/usr/X11/include',
                                '/usr/include']

if os.path.join(sys.prefix, 'lib') not in default_lib_dirs:
    default_lib_dirs.insert(0,os.path.join(sys.prefix, 'lib'))
    default_include_dirs.append(os.path.join(sys.prefix, 'include'))
    default_src_dirs.append(os.path.join(sys.prefix, 'src'))

default_lib_dirs = filter(os.path.isdir, default_lib_dirs)
default_include_dirs = filter(os.path.isdir, default_include_dirs)
default_src_dirs = filter(os.path.isdir, default_src_dirs)

so_ext = distutils.sysconfig.get_config_vars('SO')[0] or ''

def get_standard_file(fname):
    """Returns a list of files named 'fname' from
    1) System-wide directory (directory-location of this module)
    2) Users HOME directory (os.environ['HOME'])
    3) Local directory
    """
    # System-wide file
    filenames = []
    try:
        f = __file__
    except NameError:
        f = sys.argv[0]
    else:
        sysfile = os.path.join(os.path.split(os.path.abspath(f))[0],
                               fname)
        if os.path.isfile(sysfile):
            filenames.append(sysfile)

    # Home directory
    # And look for the user config file
    try:
        f = os.environ['HOME']
    except KeyError:
        pass
    else:
        user_file = os.path.join(f, fname)
        if os.path.isfile(user_file):
            filenames.append(user_file)

    # Local file
    if os.path.isfile(fname):
        filenames.append(os.path.abspath(fname))

    return filenames

def get_info(name,notfound_action=0):
    """
    notfound_action:
      0 - do nothing
      1 - display warning message
      2 - raise error
    """
    cl = {'atlas':atlas_info,  # use lapack_opt or blas_opt instead
          'atlas_threads':atlas_threads_info,                # ditto
          'atlas_blas':atlas_blas_info,
          'atlas_blas_threads':atlas_blas_threads_info,
          'lapack_atlas':lapack_atlas_info,  # use lapack_opt instead
          'lapack_atlas_threads':lapack_atlas_threads_info,  # ditto
          'mkl':mkl_info,
          'lapack_mkl':lapack_mkl_info,      # use lapack_opt instead
          'blas_mkl':blas_mkl_info,          # use blas_opt instead
          'x11':x11_info,
          'fft_opt':fft_opt_info,
          'fftw':fftw_info,
          'fftw2':fftw2_info,
          'fftw3':fftw3_info,
          'dfftw':dfftw_info,
          'sfftw':sfftw_info,
          'fftw_threads':fftw_threads_info,
          'dfftw_threads':dfftw_threads_info,
          'sfftw_threads':sfftw_threads_info,
          'djbfft':djbfft_info,
          'blas':blas_info,                  # use blas_opt instead
          'lapack':lapack_info,              # use lapack_opt instead
          'lapack_src':lapack_src_info,
          'blas_src':blas_src_info,
          'numpy':numpy_info,
          'f2py':f2py_info,
          'Numeric':Numeric_info,
          'numeric':Numeric_info,
          'numarray':numarray_info,
          'numerix':numerix_info,
          'lapack_opt':lapack_opt_info,
          'blas_opt':blas_opt_info,
          'boost_python':boost_python_info,
          'agg2':agg2_info,
          'wx':wx_info,
          'gdk_pixbuf_xlib_2':gdk_pixbuf_xlib_2_info,
          'gdk-pixbuf-xlib-2.0':gdk_pixbuf_xlib_2_info,
          'gdk_pixbuf_2':gdk_pixbuf_2_info,
          'gdk-pixbuf-2.0':gdk_pixbuf_2_info,
          'gdk':gdk_info,
          'gdk_2':gdk_2_info,
          'gdk-2.0':gdk_2_info,
          'gdk_x11_2':gdk_x11_2_info,
          'gdk-x11-2.0':gdk_x11_2_info,
          'gtkp_x11_2':gtkp_x11_2_info,
          'gtk+-x11-2.0':gtkp_x11_2_info,
          'gtkp_2':gtkp_2_info,
          'gtk+-2.0':gtkp_2_info,
          'xft':xft_info,
          'freetype2':freetype2_info,
          'umfpack':umfpack_info,
          'amd':amd_info,
          }.get(name.lower(),system_info)
    return cl().get_info(notfound_action)

class NotFoundError(DistutilsError):
    """Some third-party program or library is not found."""

class AtlasNotFoundError(NotFoundError):
    """
    Atlas (http://math-atlas.sourceforge.net/) libraries not found.
    Directories to search for the libraries can be specified in the
    numpy/distutils/site.cfg file (section [atlas]) or by setting
    the ATLAS environment variable."""

class LapackNotFoundError(NotFoundError):
    """
    Lapack (http://www.netlib.org/lapack/) libraries not found.
    Directories to search for the libraries can be specified in the
    numpy/distutils/site.cfg file (section [lapack]) or by setting
    the LAPACK environment variable."""

class LapackSrcNotFoundError(LapackNotFoundError):
    """
    Lapack (http://www.netlib.org/lapack/) sources not found.
    Directories to search for the sources can be specified in the
    numpy/distutils/site.cfg file (section [lapack_src]) or by setting
    the LAPACK_SRC environment variable."""

class BlasNotFoundError(NotFoundError):
    """
    Blas (http://www.netlib.org/blas/) libraries not found.
    Directories to search for the libraries can be specified in the
    numpy/distutils/site.cfg file (section [blas]) or by setting
    the BLAS environment variable."""

class BlasSrcNotFoundError(BlasNotFoundError):
    """
    Blas (http://www.netlib.org/blas/) sources not found.
    Directories to search for the sources can be specified in the
    numpy/distutils/site.cfg file (section [blas_src]) or by setting
    the BLAS_SRC environment variable."""

class FFTWNotFoundError(NotFoundError):
    """
    FFTW (http://www.fftw.org/) libraries not found.
    Directories to search for the libraries can be specified in the
    numpy/distutils/site.cfg file (section [fftw]) or by setting
    the FFTW environment variable."""

class DJBFFTNotFoundError(NotFoundError):
    """
    DJBFFT (http://cr.yp.to/djbfft.html) libraries not found.
    Directories to search for the libraries can be specified in the
    numpy/distutils/site.cfg file (section [djbfft]) or by setting
    the DJBFFT environment variable."""

class NumericNotFoundError(NotFoundError):
    """
    Numeric (http://www.numpy.org/) module not found.
    Get it from above location, install it, and retry setup.py."""

class X11NotFoundError(NotFoundError):
    """X11 libraries not found."""

class UmfpackNotFoundError(NotFoundError):
    """
    UMFPACK sparse solver (http://www.cise.ufl.edu/research/sparse/umfpack/)
    not found. Directories to search for the libraries can be specified in the
    numpy/distutils/site.cfg file (section [umfpack]) or by setting
    the UMFPACK environment variable."""

class system_info:

    """ get_info() is the only public method. Don't use others.
    """
    section = 'DEFAULT'
    dir_env_var = None
    search_static_first = 0 # XXX: disabled by default, may disappear in
                            # future unless it is proved to be useful.
    verbosity = 1
    saved_results = {}

    notfounderror = NotFoundError

    def __init__ (self,
                  default_lib_dirs=default_lib_dirs,
                  default_include_dirs=default_include_dirs,
                  verbosity = 1,
                  ):
        self.__class__.info = {}
        self.local_prefixes = []
        defaults = {}
        defaults['libraries'] = ''
        defaults['library_dirs'] = os.pathsep.join(default_lib_dirs)
        defaults['include_dirs'] = os.pathsep.join(default_include_dirs)
        defaults['src_dirs'] = os.pathsep.join(default_src_dirs)
        defaults['search_static_first'] = str(self.search_static_first)
        self.cp = ConfigParser.ConfigParser(defaults)
        self.files = get_standard_file('site.cfg')
        self.parse_config_files()
        self.search_static_first = self.cp.getboolean(self.section,
                                                      'search_static_first')
        assert isinstance(self.search_static_first, int)

    def parse_config_files(self):
        self.cp.read(self.files)
        if not self.cp.has_section(self.section):
            self.cp.add_section(self.section)

    def calc_libraries_info(self):
        libs = self.get_libraries()
        dirs = self.get_lib_dirs()
        info = {}
        for lib in libs:
            i = None
            for d in dirs:
                i = self.check_libs(d,[lib])
                if i is not None:
                    break
            if i is not None:
                dict_append(info,**i)
            else:
                log.info('Library %s was not found. Ignoring' % (lib))
        return info

    def set_info(self,**info):
        if info:
            lib_info = self.calc_libraries_info()
            dict_append(info,**lib_info)
        self.saved_results[self.__class__.__name__] = info

    def has_info(self):
        return self.saved_results.has_key(self.__class__.__name__)

    def get_info(self,notfound_action=0):
        """ Return a dictonary with items that are compatible
            with numpy.distutils.setup keyword arguments.
        """
        flag = 0
        if not self.has_info():
            flag = 1
            log.info(self.__class__.__name__ + ':')
            if hasattr(self, 'calc_info'):
                self.calc_info()
            if notfound_action:
                if not self.has_info():
                    if notfound_action==1:
                        warnings.warn(self.notfounderror.__doc__)
                    elif notfound_action==2:
                        raise self.notfounderror,self.notfounderror.__doc__
                    else:
                        raise ValueError(repr(notfound_action))

            if not self.has_info():
                log.info('  NOT AVAILABLE')
                self.set_info()
            else:
                log.info('  FOUND:')

        res = self.saved_results.get(self.__class__.__name__)
        if self.verbosity>0 and flag:
            for k,v in res.items():
                v = str(v)
                if k=='sources' and len(v)>200: v = v[:60]+' ...\n... '+v[-60:]
                log.info('    %s = %s', k, v)
            log.info('')

        return copy.deepcopy(res)

    def get_paths(self, section, key):
        dirs = self.cp.get(section, key).split(os.pathsep)
        env_var = self.dir_env_var
        if env_var:
            if is_sequence(env_var):
                e0 = env_var[-1]
                for e in env_var:
                    if os.environ.has_key(e):
                        e0 = e
                        break
                if not env_var[0]==e0:
                    log.info('Setting %s=%s' % (env_var[0],e0))
                env_var = e0
        if env_var and os.environ.has_key(env_var):
            d = os.environ[env_var]
            if d=='None':
                log.info('Disabled %s: %s',self.__class__.__name__,'(%s is None)' \
                      % (env_var,))
                return []
            if os.path.isfile(d):
                dirs = [os.path.dirname(d)] + dirs
                l = getattr(self,'_lib_names',[])
                if len(l)==1:
                    b = os.path.basename(d)
                    b = os.path.splitext(b)[0]
                    if b[:3]=='lib':
                        log.info('Replacing _lib_names[0]==%r with %r' \
                              % (self._lib_names[0], b[3:]))
                        self._lib_names[0] = b[3:]
            else:
                ds = d.split(os.pathsep)
                ds2 = []
                for d in ds:
                    if os.path.isdir(d):
                        ds2.append(d)
                        for dd in ['include','lib']:
                            d1 = os.path.join(d,dd)
                            if os.path.isdir(d1):
                                ds2.append(d1)
                dirs = ds2 + dirs
        default_dirs = self.cp.get('DEFAULT', key).split(os.pathsep)
        dirs.extend(default_dirs)
        ret = []
        for d in dirs:
            if os.path.isdir(d) and d not in ret:
                ret.append(d)
        log.debug('( %s = %s )', key, ':'.join(ret))
        return ret

    def get_lib_dirs(self, key='library_dirs'):
        return self.get_paths(self.section, key)

    def get_include_dirs(self, key='include_dirs'):
        return self.get_paths(self.section, key)

    def get_src_dirs(self, key='src_dirs'):
        return self.get_paths(self.section, key)

    def get_libs(self, key, default):
        try:
            libs = self.cp.get(self.section, key)
        except ConfigParser.NoOptionError:
            if not default:
                return []
            if is_string(default):
                return [default]
            return default
        return [b for b in [a.strip() for a in libs.split(',')] if b]

    def get_libraries(self, key='libraries'):
        return self.get_libs(key,'')

    def library_extensions(self):
        static_exts = ['.a']
        if sys.platform == 'win32':
            static_exts.append('.lib')  # .lib is used by MSVC
        if self.search_static_first:
            exts = static_exts + [so_ext]
        else:
            exts = [so_ext] + static_exts
        if sys.platform == 'cygwin':
            exts.append('.dll.a')
        return exts

    def check_libs(self,lib_dir,libs,opt_libs =[]):
        """If static or shared libraries are available then return
        their info dictionary.

        Checks for all libraries as shared libraries first, then
        static (or vice versa if self.search_static_first is True).
        """
        exts = self.library_extensions()
        info = None
        for ext in exts:
            info = self._check_libs(lib_dir,libs,opt_libs,[ext])
            if info is not None:
                break
        if not info:
            log.info('  libraries %s not found in %s', ','.join(libs), lib_dir)
        return info

    def check_libs2(self, lib_dir, libs, opt_libs =[]):
        """If static or shared libraries are available then return
        their info dictionary.

        Checks each library for shared or static.
        """
        exts = self.library_extensions()
        info = self._check_libs(lib_dir,libs,opt_libs,exts)
        if not info:
            log.info('  libraries %s not found in %s', ','.join(libs), lib_dir)
        return info

    def _lib_list(self, lib_dir, libs, exts):
        assert is_string(lib_dir)
        liblist = []
        # under windows first try without 'lib' prefix
        if sys.platform == 'win32':
            lib_prefixes = ['', 'lib']
        else:
            lib_prefixes = ['lib']
        # for each library name, see if we can find a file for it.
        for l in libs:
            for ext in exts:
                for prefix in lib_prefixes:
                    p = self.combine_paths(lib_dir, prefix+l+ext)
                    if p:
                        break
                if p:
                    assert len(p)==1
                    # ??? splitext on p[0] would do this for cygwin
                    # doesn't seem correct
                    if ext == '.dll.a':
                        l += '.dll'
                    liblist.append(l)
                    break
        return liblist

    def _check_libs(self, lib_dir, libs, opt_libs, exts):
        found_libs = self._lib_list(lib_dir, libs, exts)
        if len(found_libs) == len(libs):
            info = {'libraries' : found_libs, 'library_dirs' : [lib_dir]}
            opt_found_libs = self._lib_list(lib_dir, opt_libs, exts)
            if len(opt_found_libs) == len(opt_libs):
                info['libraries'].extend(opt_found_libs)
            return info
        else:
            return None

    def combine_paths(self,*args):
        """Return a list of existing paths composed by all combinations
        of items from the arguments.
        """
        return combine_paths(*args,**{'verbosity':self.verbosity})


class fft_opt_info(system_info):

    def calc_info(self):
        info = {}
        fftw_info = get_info('fftw3') or get_info('fftw2') or get_info('dfftw')
        djbfft_info = get_info('djbfft')
        if fftw_info:
            dict_append(info,**fftw_info)
            if djbfft_info:
                dict_append(info,**djbfft_info)
            self.set_info(**info)
            return


class fftw_info(system_info):
    #variables to override
    section = 'fftw'
    dir_env_var = 'FFTW'
    notfounderror = FFTWNotFoundError
    ver_info  = [ { 'name':'fftw3',
                    'libs':['fftw3'],
                    'includes':['fftw3.h'],
                    'macros':[('SCIPY_FFTW3_H',None)]},
                  { 'name':'fftw2',
                    'libs':['rfftw', 'fftw'],
                    'includes':['fftw.h','rfftw.h'],
                    'macros':[('SCIPY_FFTW_H',None)]}]

    def __init__(self):
        system_info.__init__(self)

    def calc_ver_info(self,ver_param):
        """Returns True on successful version detection, else False"""
        lib_dirs = self.get_lib_dirs()
        incl_dirs = self.get_include_dirs()
        incl_dir = None
        libs = self.get_libs(self.section+'_libs', ver_param['libs'])
        info = None
        for d in lib_dirs:
            r = self.check_libs(d,libs)
            if r is not None:
                info = r
                break
        if info is not None:
            flag = 0
            for d in incl_dirs:
                if len(self.combine_paths(d,ver_param['includes']))==len(ver_param['includes']):
                    dict_append(info,include_dirs=[d])
                    flag = 1
                    incl_dirs = [d]
                    incl_dir = d
                    break
            if flag:
                dict_append(info,define_macros=ver_param['macros'])
            else:
                info = None
        if info is not None:
            self.set_info(**info)
            return True
        else:
            log.info('  %s not found' % (ver_param['name']))
            return False

    def calc_info(self):
        for i in self.ver_info:
            if self.calc_ver_info(i):
                break

class fftw2_info(fftw_info):
    #variables to override
    section = 'fftw'
    dir_env_var = 'FFTW'
    notfounderror = FFTWNotFoundError
    ver_info  = [ { 'name':'fftw2',
                    'libs':['rfftw', 'fftw'],
                    'includes':['fftw.h','rfftw.h'],
                    'macros':[('SCIPY_FFTW_H',None)]}
                  ]

class fftw3_info(fftw_info):
    #variables to override
    section = 'fftw3'
    dir_env_var = 'FFTW3'
    notfounderror = FFTWNotFoundError
    ver_info  = [ { 'name':'fftw3',
                    'libs':['fftw3'],
                    'includes':['fftw3.h'],
                    'macros':[('SCIPY_FFTW3_H',None)]},
                  ]

class dfftw_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    ver_info  = [ { 'name':'dfftw',
                    'libs':['drfftw','dfftw'],
                    'includes':['dfftw.h','drfftw.h'],
                    'macros':[('SCIPY_DFFTW_H',None)]} ]

class sfftw_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    ver_info  = [ { 'name':'sfftw',
                    'libs':['srfftw','sfftw'],
                    'includes':['sfftw.h','srfftw.h'],
                    'macros':[('SCIPY_SFFTW_H',None)]} ]

class fftw_threads_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    ver_info  = [ { 'name':'fftw threads',
                    'libs':['rfftw_threads','fftw_threads'],
                    'includes':['fftw_threads.h','rfftw_threads.h'],
                    'macros':[('SCIPY_FFTW_THREADS_H',None)]} ]

class dfftw_threads_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    ver_info  = [ { 'name':'dfftw threads',
                    'libs':['drfftw_threads','dfftw_threads'],
                    'includes':['dfftw_threads.h','drfftw_threads.h'],
                    'macros':[('SCIPY_DFFTW_THREADS_H',None)]} ]

class sfftw_threads_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    ver_info  = [ { 'name':'sfftw threads',
                    'libs':['srfftw_threads','sfftw_threads'],
                    'includes':['sfftw_threads.h','srfftw_threads.h'],
                    'macros':[('SCIPY_SFFTW_THREADS_H',None)]} ]

class djbfft_info(system_info):
    section = 'djbfft'
    dir_env_var = 'DJBFFT'
    notfounderror = DJBFFTNotFoundError

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend(self.combine_paths(d,['djbfft'])+[d])
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()
        incl_dirs = self.get_include_dirs()
        info = None
        for d in lib_dirs:
            p = self.combine_paths (d,['djbfft.a'])
            if p:
                info = {'extra_objects':p}
                break
            p = self.combine_paths (d,['libdjbfft.a','libdjbfft'+so_ext])
            if p:
                info = {'libraries':['djbfft'],'library_dirs':[d]}
                break
        if info is None:
            return
        for d in incl_dirs:
            if len(self.combine_paths(d,['fftc8.h','fftfreq.h']))==2:
                dict_append(info,include_dirs=[d],
                            define_macros=[('SCIPY_DJBFFT_H',None)])
                self.set_info(**info)
                return
        return

class mkl_info(system_info):
    section = 'mkl'
    dir_env_var = 'MKL'
    _lib_mkl = ['mkl','vml','guide']

    def get_mkl_rootdir(self):
        mklroot = os.environ.get('MKLROOT',None)
        if mklroot is not None:
            return mklroot
        paths = os.environ.get('LD_LIBRARY_PATH','').split(os.pathsep)
        ld_so_conf = '/etc/ld.so.conf'
        if os.path.isfile(ld_so_conf):
            for d in open(ld_so_conf,'r').readlines():
                d = d.strip()
                if d: paths.append(d)
        intel_mkl_dirs = []
        for path in paths:
            path_atoms = path.split(os.sep)
            for m in path_atoms:
                if m.startswith('mkl'):
                    d = os.sep.join(path_atoms[:path_atoms.index(m)+2])
                    intel_mkl_dirs.append(d)
                    break
        for d in paths:
            dirs = glob(os.path.join(d,'mkl','*')) + glob(os.path.join(d,'mkl*'))
            for d in dirs:
                if os.path.isdir(os.path.join(d,'lib')):
                    return d
        return None

    def __init__(self):
        mklroot = self.get_mkl_rootdir()
        if mklroot is None:
            system_info.__init__(self)
        else:
            from cpuinfo import cpu
            l = 'mkl' # use shared library
            if cpu.is_Itanium():
                plt = '64'
                #l = 'mkl_ipf'
            elif cpu.is_Xeon():
                plt = 'em64t'
                #l = 'mkl_em64t'
            else:
                plt = '32'
                #l = 'mkl_ia32'
            if l not in self._lib_mkl:
                self._lib_mkl.insert(0,l)
            system_info.__init__(self,
                                 default_lib_dirs=[os.path.join(mklroot,'lib',plt)],
                                 default_include_dirs=[os.path.join(mklroot,'include')])

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()
        incl_dirs = self.get_include_dirs()
        mkl_libs = self.get_libs('mkl_libs',self._lib_mkl)
        mkl = None
        for d in lib_dirs:
            mkl = self.check_libs2(d,mkl_libs)
            if mkl is not None:
                break
        if mkl is None:
            return
        info = {}
        dict_append(info,**mkl)
        dict_append(info,libraries = ['pthread'], include_dirs = incl_dirs)
        self.set_info(**info)

class lapack_mkl_info(mkl_info):

    def calc_info(self):
        mkl = get_info('mkl')
        if not mkl:
            return
        lapack_libs = self.get_libs('lapack_libs',['mkl_lapack32','mkl_lapack64'])
        info = {'libraries': lapack_libs}
        dict_append(info,**mkl)
        self.set_info(**info)

class blas_mkl_info(mkl_info):
    pass

class atlas_info(system_info):
    section = 'atlas'
    dir_env_var = 'ATLAS'
    _lib_names = ['f77blas','cblas']
    if sys.platform[:7]=='freebsd':
        _lib_atlas = ['atlas_r']
        _lib_lapack = ['alapack_r']
    else:
        _lib_atlas = ['atlas']
        _lib_lapack = ['lapack']

    notfounderror = AtlasNotFoundError

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend(self.combine_paths(d,['atlas*','ATLAS*',
                                         'sse','3dnow','sse2'])+[d])
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()
        info = {}
        atlas_libs = self.get_libs('atlas_libs',
                                   self._lib_names + self._lib_atlas)
        lapack_libs = self.get_libs('lapack_libs',self._lib_lapack)
        atlas = None
        lapack = None
        atlas_1 = None
        for d in lib_dirs:
            atlas = self.check_libs2(d,atlas_libs,[])
            lapack_atlas = self.check_libs2(d,['lapack_atlas'],[])
            if atlas is not None:
                lib_dirs2 = [d] + self.combine_paths(d,['atlas*','ATLAS*'])
                for d2 in lib_dirs2:
                    lapack = self.check_libs2(d2,lapack_libs,[])
                    if lapack is not None:
                        break
                else:
                    lapack = None
                if lapack is not None:
                    break
            if atlas:
                atlas_1 = atlas
        log.info(self.__class__)
        if atlas is None:
            atlas = atlas_1
        if atlas is None:
            return
        include_dirs = self.get_include_dirs()
        h = (self.combine_paths(lib_dirs+include_dirs,'cblas.h') or [None])[0]
        if h:
            h = os.path.dirname(h)
            dict_append(info,include_dirs=[h])
        info['language'] = 'c'
        if lapack is not None:
            dict_append(info,**lapack)
            dict_append(info,**atlas)
        elif 'lapack_atlas' in atlas['libraries']:
            dict_append(info,**atlas)
            dict_append(info,define_macros=[('ATLAS_WITH_LAPACK_ATLAS',None)])
            self.set_info(**info)
            return
        else:
            dict_append(info,**atlas)
            dict_append(info,define_macros=[('ATLAS_WITHOUT_LAPACK',None)])
            message = """
*********************************************************************
    Could not find lapack library within the ATLAS installation.
*********************************************************************
"""
            warnings.warn(message)
            self.set_info(**info)
            return

        # Check if lapack library is complete, only warn if it is not.
        lapack_dir = lapack['library_dirs'][0]
        lapack_name = lapack['libraries'][0]
        lapack_lib = None
        lib_prefixes = ['lib']
        if sys.platform == 'win32':
            lib_prefixes.append('')
        for e in self.library_extensions():
            for prefix in lib_prefixes:
                fn = os.path.join(lapack_dir,prefix+lapack_name+e)
                if os.path.exists(fn):
                    lapack_lib = fn
                    break
            if lapack_lib:
                break
        if lapack_lib is not None:
            sz = os.stat(lapack_lib)[6]
            if sz <= 4000*1024:
                message = """
*********************************************************************
    Lapack library (from ATLAS) is probably incomplete:
      size of %s is %sk (expected >4000k)

    Follow the instructions in the KNOWN PROBLEMS section of the file
    numpy/INSTALL.txt.
*********************************************************************
""" % (lapack_lib,sz/1024)
                warnings.warn(message)
            else:
                info['language'] = 'f77'

        self.set_info(**info)

class atlas_blas_info(atlas_info):
    _lib_names = ['f77blas','cblas']

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()
        info = {}
        atlas_libs = self.get_libs('atlas_libs',
                                   self._lib_names + self._lib_atlas)
        atlas = None
        for d in lib_dirs:
            atlas = self.check_libs2(d,atlas_libs,[])
            if atlas is not None:
                break
        if atlas is None:
            return
        include_dirs = self.get_include_dirs()
        h = (self.combine_paths(lib_dirs+include_dirs,'cblas.h') or [None])[0]
        if h:
            h = os.path.dirname(h)
            dict_append(info,include_dirs=[h])
        info['language'] = 'c'

        dict_append(info,**atlas)

        self.set_info(**info)
        return


class atlas_threads_info(atlas_info):
    dir_env_var = ['PTATLAS','ATLAS']
    _lib_names = ['ptf77blas','ptcblas']

class atlas_blas_threads_info(atlas_blas_info):
    dir_env_var = ['PTATLAS','ATLAS']
    _lib_names = ['ptf77blas','ptcblas']

class lapack_atlas_info(atlas_info):
    _lib_names = ['lapack_atlas'] + atlas_info._lib_names

class lapack_atlas_threads_info(atlas_threads_info):
    _lib_names = ['lapack_atlas'] + atlas_threads_info._lib_names

class lapack_info(system_info):
    section = 'lapack'
    dir_env_var = 'LAPACK'
    _lib_names = ['lapack']
    notfounderror = LapackNotFoundError

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()

        lapack_libs = self.get_libs('lapack_libs', self._lib_names)
        for d in lib_dirs:
            lapack = self.check_libs(d,lapack_libs,[])
            if lapack is not None:
                info = lapack
                break
        else:
            return
        info['language'] = 'f77'
        self.set_info(**info)

class lapack_src_info(system_info):
    section = 'lapack_src'
    dir_env_var = 'LAPACK_SRC'
    notfounderror = LapackSrcNotFoundError

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend([d] + self.combine_paths(d,['LAPACK*/SRC','SRC']))
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        src_dirs = self.get_src_dirs()
        src_dir = ''
        for d in src_dirs:
            if os.path.isfile(os.path.join(d,'dgesv.f')):
                src_dir = d
                break
        if not src_dir:
            #XXX: Get sources from netlib. May be ask first.
            return
        # The following is extracted from LAPACK-3.0/SRC/Makefile
        allaux='''
        ilaenv ieeeck lsame lsamen xerbla
        ''' # *.f
        laux = '''
        bdsdc bdsqr disna labad lacpy ladiv lae2 laebz laed0 laed1
        laed2 laed3 laed4 laed5 laed6 laed7 laed8 laed9 laeda laev2
        lagtf lagts lamch lamrg lanst lapy2 lapy3 larnv larrb larre
        larrf lartg laruv las2 lascl lasd0 lasd1 lasd2 lasd3 lasd4
        lasd5 lasd6 lasd7 lasd8 lasd9 lasda lasdq lasdt laset lasq1
        lasq2 lasq3 lasq4 lasq5 lasq6 lasr lasrt lassq lasv2 pttrf
        stebz stedc steqr sterf
        ''' # [s|d]*.f
        lasrc = '''
        gbbrd gbcon gbequ gbrfs gbsv gbsvx gbtf2 gbtrf gbtrs gebak
        gebal gebd2 gebrd gecon geequ gees geesx geev geevx gegs gegv
        gehd2 gehrd gelq2 gelqf gels gelsd gelss gelsx gelsy geql2
        geqlf geqp3 geqpf geqr2 geqrf gerfs gerq2 gerqf gesc2 gesdd
        gesv gesvd gesvx getc2 getf2 getrf getri getrs ggbak ggbal
        gges ggesx ggev ggevx ggglm gghrd gglse ggqrf ggrqf ggsvd
        ggsvp gtcon gtrfs gtsv gtsvx gttrf gttrs gtts2 hgeqz hsein
        hseqr labrd lacon laein lags2 lagtm lahqr lahrd laic1 lals0
        lalsa lalsd langb lange langt lanhs lansb lansp lansy lantb
        lantp lantr lapll lapmt laqgb laqge laqp2 laqps laqsb laqsp
        laqsy lar1v lar2v larf larfb larfg larft larfx largv larrv
        lartv larz larzb larzt laswp lasyf latbs latdf latps latrd
        latrs latrz latzm lauu2 lauum pbcon pbequ pbrfs pbstf pbsv
        pbsvx pbtf2 pbtrf pbtrs pocon poequ porfs posv posvx potf2
        potrf potri potrs ppcon ppequ pprfs ppsv ppsvx pptrf pptri
        pptrs ptcon pteqr ptrfs ptsv ptsvx pttrs ptts2 spcon sprfs
        spsv spsvx sptrf sptri sptrs stegr stein sycon syrfs sysv
        sysvx sytf2 sytrf sytri sytrs tbcon tbrfs tbtrs tgevc tgex2
        tgexc tgsen tgsja tgsna tgsy2 tgsyl tpcon tprfs tptri tptrs
        trcon trevc trexc trrfs trsen trsna trsyl trti2 trtri trtrs
        tzrqf tzrzf
        ''' # [s|c|d|z]*.f
        sd_lasrc = '''
        laexc lag2 lagv2 laln2 lanv2 laqtr lasy2 opgtr opmtr org2l
        org2r orgbr orghr orgl2 orglq orgql orgqr orgr2 orgrq orgtr
        orm2l orm2r ormbr ormhr orml2 ormlq ormql ormqr ormr2 ormr3
        ormrq ormrz ormtr rscl sbev sbevd sbevx sbgst sbgv sbgvd sbgvx
        sbtrd spev spevd spevx spgst spgv spgvd spgvx sptrd stev stevd
        stevr stevx syev syevd syevr syevx sygs2 sygst sygv sygvd
        sygvx sytd2 sytrd
        ''' # [s|d]*.f
        cz_lasrc = '''
        bdsqr hbev hbevd hbevx hbgst hbgv hbgvd hbgvx hbtrd hecon heev
        heevd heevr heevx hegs2 hegst hegv hegvd hegvx herfs hesv
        hesvx hetd2 hetf2 hetrd hetrf hetri hetrs hpcon hpev hpevd
        hpevx hpgst hpgv hpgvd hpgvx hprfs hpsv hpsvx hptrd hptrf
        hptri hptrs lacgv lacp2 lacpy lacrm lacrt ladiv laed0 laed7
        laed8 laesy laev2 lahef lanhb lanhe lanhp lanht laqhb laqhe
        laqhp larcm larnv lartg lascl laset lasr lassq pttrf rot spmv
        spr stedc steqr symv syr ung2l ung2r ungbr unghr ungl2 unglq
        ungql ungqr ungr2 ungrq ungtr unm2l unm2r unmbr unmhr unml2
        unmlq unmql unmqr unmr2 unmr3 unmrq unmrz unmtr upgtr upmtr
        ''' # [c|z]*.f
        #######
        sclaux = laux + ' econd '                  # s*.f
        dzlaux = laux + ' secnd '                  # d*.f
        slasrc = lasrc + sd_lasrc                  # s*.f
        dlasrc = lasrc + sd_lasrc                  # d*.f
        clasrc = lasrc + cz_lasrc + ' srot srscl ' # c*.f
        zlasrc = lasrc + cz_lasrc + ' drot drscl ' # z*.f
        oclasrc = ' icmax1 scsum1 '                # *.f
        ozlasrc = ' izmax1 dzsum1 '                # *.f
        sources = ['s%s.f'%f for f in (sclaux+slasrc).split()] \
                  + ['d%s.f'%f for f in (dzlaux+dlasrc).split()] \
                  + ['c%s.f'%f for f in (clasrc).split()] \
                  + ['z%s.f'%f for f in (zlasrc).split()] \
                  + ['%s.f'%f for f in (allaux+oclasrc+ozlasrc).split()]
        sources = [os.path.join(src_dir,f) for f in sources]
        #XXX: should we check here actual existence of source files?
        info = {'sources':sources,'language':'f77'}
        self.set_info(**info)

atlas_version_c_text = r'''
/* This file is generated from numpy_distutils/system_info.py */
void ATL_buildinfo(void);
int main(void) {
  ATL_buildinfo();
  return 0;
}
'''

_cached_atlas_version = {}
def get_atlas_version(**config):
    libraries = config.get('libraries', [])
    library_dirs = config.get('library_dirs', [])
    key = (tuple(libraries), tuple(library_dirs))
    if _cached_atlas_version.has_key(key):
        return _cached_atlas_version[key]
    c = cmd_config(Distribution())
    atlas_version = None  
    try:
        s, o = c.get_output(atlas_version_c_text,
                            libraries=libraries, library_dirs=library_dirs)
    except: # failed to get version from file -- maybe on Windows
        # look at directory name
        for o in library_dirs:
            m = re.search(r'ATLAS_(?P<version>\d+[.]\d+[.]\d+)_',o)
            if m:
                atlas_version = m.group('version')
            if atlas_version is not None:
                break
        # final choice --- look at ATLAS_VERSION environment
        #   variable
        if atlas_version is None:
            atlas_version = os.environ.get('ATLAS_VERSION',None)
        return atlas_version or '?.?.?'

    if not s:
        m = re.search(r'ATLAS version (?P<version>\d+[.]\d+[.]\d+)',o)
        if m:
            atlas_version = m.group('version')
    if atlas_version is None:
        if re.search(r'undefined symbol: ATL_buildinfo',o,re.M):
            atlas_version = '3.2.1_pre3.3.6'
        else:
            log.info('Status: %d', s)
            log.info('Output: %s', o)
    _cached_atlas_version[key] = atlas_version
    return atlas_version

from distutils.util import get_platform

class lapack_opt_info(system_info):

    def calc_info(self):

        if sys.platform=='darwin' and not os.environ.get('ATLAS',None):
            args = []
            link_args = []
            if get_platform()[-4:] == 'i386':
                intel = 1
            else:
                intel = 0
            if os.path.exists('/System/Library/Frameworks/Accelerate.framework/'):
                if intel:
                    args.extend(['-msse3'])
                else:
                    args.extend(['-faltivec'])
                link_args.extend(['-Wl,-framework','-Wl,Accelerate'])
            elif os.path.exists('/System/Library/Frameworks/vecLib.framework/'):
                if intel:
                    args.extend(['-msse3'])
                else:
                    args.extend(['-faltivec'])
                link_args.extend(['-Wl,-framework','-Wl,vecLib'])
            if args:
                self.set_info(extra_compile_args=args,
                              extra_link_args=link_args,
                              define_macros=[('NO_ATLAS_INFO',3)])
                return

        lapack_mkl_info = get_info('lapack_mkl')
        if lapack_mkl_info:
            self.set_info(**lapack_mkl_info)
            return

        atlas_info = get_info('atlas_threads')
        if not atlas_info:
            atlas_info = get_info('atlas')
        #atlas_info = {} ## uncomment for testing
        atlas_version = None
        need_lapack = 0
        need_blas = 0
        info = {}
        if atlas_info:
            version_info = atlas_info.copy()
            atlas_version = get_atlas_version(**version_info)
            if not atlas_info.has_key('define_macros'):
                atlas_info['define_macros'] = []
            if atlas_version is None:
                atlas_info['define_macros'].append(('NO_ATLAS_INFO',2))
            else:
                atlas_info['define_macros'].append(('ATLAS_INFO',
                                                    '"\\"%s\\""' % atlas_version))
            if atlas_version=='3.2.1_pre3.3.6':
                atlas_info['define_macros'].append(('NO_ATLAS_INFO',4))
            l = atlas_info.get('define_macros',[])
            if ('ATLAS_WITH_LAPACK_ATLAS',None) in l \
                   or ('ATLAS_WITHOUT_LAPACK',None) in l:
                need_lapack = 1
            info = atlas_info
        else:
            warnings.warn(AtlasNotFoundError.__doc__)
            need_blas = 1
            need_lapack = 1
            dict_append(info,define_macros=[('NO_ATLAS_INFO',1)])

        if need_lapack:
            lapack_info = get_info('lapack')
            #lapack_info = {} ## uncomment for testing
            if lapack_info:
                dict_append(info,**lapack_info)
            else:
                warnings.warn(LapackNotFoundError.__doc__)
                lapack_src_info = get_info('lapack_src')
                if not lapack_src_info:
                    warnings.warn(LapackSrcNotFoundError.__doc__)
                    return
                dict_append(info,libraries=[('flapack_src',lapack_src_info)])

        if need_blas:
            blas_info = get_info('blas')
            #blas_info = {} ## uncomment for testing
            if blas_info:
                dict_append(info,**blas_info)
            else:
                warnings.warn(BlasNotFoundError.__doc__)
                blas_src_info = get_info('blas_src')
                if not blas_src_info:
                    warnings.warn(BlasSrcNotFoundError.__doc__)
                    return
                dict_append(info,libraries=[('fblas_src',blas_src_info)])

        self.set_info(**info)
        return


class blas_opt_info(system_info):

    def calc_info(self):

        if sys.platform=='darwin' and not os.environ.get('ATLAS',None):
            args = []
            link_args = []
            if get_platform()[-4:] == 'i386':
                intel = 1
            else:
                intel = 0
            if os.path.exists('/System/Library/Frameworks/Accelerate.framework/'):
                if intel:
                    args.extend(['-msse3'])
                else:
                    args.extend(['-faltivec'])
                args.extend([
                    '-I/System/Library/Frameworks/vecLib.framework/Headers'])
                link_args.extend(['-Wl,-framework','-Wl,Accelerate'])
            elif os.path.exists('/System/Library/Frameworks/vecLib.framework/'):
                if intel:
                    args.extend(['-msse3'])
                else:
                    args.extend(['-faltivec'])
                args.extend([
                    '-I/System/Library/Frameworks/vecLib.framework/Headers'])
                link_args.extend(['-Wl,-framework','-Wl,vecLib'])
            if args:
                self.set_info(extra_compile_args=args,
                              extra_link_args=link_args,
                              define_macros=[('NO_ATLAS_INFO',3)])
                return

        blas_mkl_info = get_info('blas_mkl')
        if blas_mkl_info:
            self.set_info(**blas_mkl_info)
            return

        atlas_info = get_info('atlas_blas_threads')
        if not atlas_info:
            atlas_info = get_info('atlas_blas')
        atlas_version = None
        need_blas = 0
        info = {}
        if atlas_info:
            version_info = atlas_info.copy()
            atlas_version = get_atlas_version(**version_info)
            if not atlas_info.has_key('define_macros'):
                atlas_info['define_macros'] = []
            if atlas_version is None:
                atlas_info['define_macros'].append(('NO_ATLAS_INFO',2))
            else:
                atlas_info['define_macros'].append(('ATLAS_INFO',
                                                    '"\\"%s\\""' % atlas_version))
            info = atlas_info
        else:
            warnings.warn(AtlasNotFoundError.__doc__)
            need_blas = 1
            dict_append(info,define_macros=[('NO_ATLAS_INFO',1)])

        if need_blas:
            blas_info = get_info('blas')
            if blas_info:
                dict_append(info,**blas_info)
            else:
                warnings.warn(BlasNotFoundError.__doc__)
                blas_src_info = get_info('blas_src')
                if not blas_src_info:
                    warnings.warn(BlasSrcNotFoundError.__doc__)
                    return
                dict_append(info,libraries=[('fblas_src',blas_src_info)])

        self.set_info(**info)
        return


class blas_info(system_info):
    section = 'blas'
    dir_env_var = 'BLAS'
    _lib_names = ['blas']
    notfounderror = BlasNotFoundError

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()

        blas_libs = self.get_libs('blas_libs', self._lib_names)
        for d in lib_dirs:
            blas = self.check_libs(d,blas_libs,[])
            if blas is not None:
                info = blas
                break
        else:
            return
        info['language'] = 'f77'  # XXX: is it generally true?
        self.set_info(**info)


class blas_src_info(system_info):
    section = 'blas_src'
    dir_env_var = 'BLAS_SRC'
    notfounderror = BlasSrcNotFoundError

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend([d] + self.combine_paths(d,['blas']))
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        src_dirs = self.get_src_dirs()
        src_dir = ''
        for d in src_dirs:
            if os.path.isfile(os.path.join(d,'daxpy.f')):
                src_dir = d
                break
        if not src_dir:
            #XXX: Get sources from netlib. May be ask first.
            return
        blas1 = '''
        caxpy csscal dnrm2 dzasum saxpy srotg zdotc ccopy cswap drot
        dznrm2 scasum srotm zdotu cdotc dasum drotg icamax scnrm2
        srotmg zdrot cdotu daxpy drotm idamax scopy sscal zdscal crotg
        dcabs1 drotmg isamax sdot sswap zrotg cscal dcopy dscal izamax
        snrm2 zaxpy zscal csrot ddot dswap sasum srot zcopy zswap
        '''
        blas2 = '''
        cgbmv chpmv ctrsv dsymv dtrsv sspr2 strmv zhemv ztpmv cgemv
        chpr dgbmv dsyr lsame ssymv strsv zher ztpsv cgerc chpr2 dgemv
        dsyr2 sgbmv ssyr xerbla zher2 ztrmv cgeru ctbmv dger dtbmv
        sgemv ssyr2 zgbmv zhpmv ztrsv chbmv ctbsv dsbmv dtbsv sger
        stbmv zgemv zhpr chemv ctpmv dspmv dtpmv ssbmv stbsv zgerc
        zhpr2 cher ctpsv dspr dtpsv sspmv stpmv zgeru ztbmv cher2
        ctrmv dspr2 dtrmv sspr stpsv zhbmv ztbsv
        '''
        blas3 = '''
        cgemm csymm ctrsm dsyrk sgemm strmm zhemm zsyr2k chemm csyr2k
        dgemm dtrmm ssymm strsm zher2k zsyrk cher2k csyrk dsymm dtrsm
        ssyr2k zherk ztrmm cherk ctrmm dsyr2k ssyrk zgemm zsymm ztrsm
        '''
        sources = [os.path.join(src_dir,f+'.f') \
                   for f in (blas1+blas2+blas3).split()]
        #XXX: should we check here actual existence of source files?
        info = {'sources':sources,'language':'f77'}
        self.set_info(**info)

class x11_info(system_info):
    section = 'x11'
    notfounderror = X11NotFoundError

    def __init__(self):
        system_info.__init__(self,
                             default_lib_dirs=default_x11_lib_dirs,
                             default_include_dirs=default_x11_include_dirs)

    def calc_info(self):
        if sys.platform  in ['win32']:
            return
        lib_dirs = self.get_lib_dirs()
        include_dirs = self.get_include_dirs()
        x11_libs = self.get_libs('x11_libs', ['X11'])
        for lib_dir in lib_dirs:
            info = self.check_libs(lib_dir, x11_libs, [])
            if info is not None:
                break
        else:
            return
        inc_dir = None
        for d in include_dirs:
            if self.combine_paths(d, 'X11/X.h'):
                inc_dir = d
                break
        if inc_dir is not None:
            dict_append(info, include_dirs=[inc_dir])
        self.set_info(**info)

class _numpy_info(system_info):
    section = 'Numeric'
    modulename = 'Numeric'
    notfounderror = NumericNotFoundError

    def __init__(self):
        include_dirs = []
        try:
            module = __import__(self.modulename)
            prefix = []
            for name in module.__file__.split(os.sep):
                if name=='lib':
                    break
                prefix.append(name)
            include_dirs.append(distutils.sysconfig.get_python_inc(
                                        prefix=os.sep.join(prefix)))
        except ImportError:
            pass
        py_incl_dir = distutils.sysconfig.get_python_inc()
        include_dirs.append(py_incl_dir)
        for d in default_include_dirs:
            d = os.path.join(d, os.path.basename(py_incl_dir))
            if d not in include_dirs:
                include_dirs.append(d)
        system_info.__init__(self,
                             default_lib_dirs=[],
                             default_include_dirs=include_dirs)

    def calc_info(self):
        try:
            module = __import__(self.modulename)
        except ImportError:
            return
        info = {}
        macros = []
        for v in ['__version__','version']:
            vrs = getattr(module,v,None)
            if vrs is None:
                continue
            macros = [(self.modulename.upper()+'_VERSION',
                      '"\\"%s\\""' % (vrs)),
                      (self.modulename.upper(),None)]
            break
##         try:
##             macros.append(
##                 (self.modulename.upper()+'_VERSION_HEX',
##                  hex(vstr2hex(module.__version__))),
##                 )
##         except Exception,msg:
##             print msg
        dict_append(info, define_macros = macros)
        include_dirs = self.get_include_dirs()
        inc_dir = None
        for d in include_dirs:
            if self.combine_paths(d,
                                  os.path.join(self.modulename,
                                               'arrayobject.h')):
                inc_dir = d
                break
        if inc_dir is not None:
            dict_append(info, include_dirs=[inc_dir])
        if info:
            self.set_info(**info)
        return

class numarray_info(_numpy_info):
    section = 'numarray'
    modulename = 'numarray'

class Numeric_info(_numpy_info):
    section = 'Numeric'
    modulename = 'Numeric'

class numpy_info(_numpy_info):
    section = 'numpy'
    modulename = 'numpy'

class numerix_info(system_info):
    section = 'numerix'
    def calc_info(self):
        which = None, None
        if os.getenv("NUMERIX"):
            which = os.getenv("NUMERIX"), "environment var"
        # If all the above fail, default to numpy.
        if which[0] is None:
            which = "numpy", "defaulted"
            try:
                import numpy
                which = "numpy", "defaulted"
            except ImportError,msg1:
                try:
                    import Numeric
                    which = "numeric", "defaulted"
                except ImportError,msg2:
                    try:
                        import numarray
                        which = "numarray", "defaulted"
                    except ImportError,msg3:
                        log.info(msg1)
                        log.info(msg2)
                        log.info(msg3)
        which = which[0].strip().lower(), which[1]
        if which[0] not in ["numeric", "numarray", "numpy"]:
            raise ValueError("numerix selector must be either 'Numeric' "
                             "or 'numarray' or 'numpy' but the value obtained"
                             " from the %s was '%s'." % (which[1], which[0]))
        os.environ['NUMERIX'] = which[0]
        self.set_info(**get_info(which[0]))

class f2py_info(system_info):
    def calc_info(self):
        try:
            import numpy.f2py as f2py
        except ImportError:
            return
        f2py_dir = os.path.join(os.path.dirname(f2py.__file__),'src')
        self.set_info(sources = [os.path.join(f2py_dir,'fortranobject.c')],
                      include_dirs = [f2py_dir])
        return

class boost_python_info(system_info):
    section = 'boost_python'
    dir_env_var = 'BOOST'

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend([d] + self.combine_paths(d,['boost*']))
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        src_dirs = self.get_src_dirs()
        src_dir = ''
        for d in src_dirs:
            if os.path.isfile(os.path.join(d,'libs','python','src','module.cpp')):
                src_dir = d
                break
        if not src_dir:
            return
        py_incl_dir = distutils.sysconfig.get_python_inc()
        srcs_dir = os.path.join(src_dir,'libs','python','src')
        bpl_srcs = glob(os.path.join(srcs_dir,'*.cpp'))
        bpl_srcs += glob(os.path.join(srcs_dir,'*','*.cpp'))
        info = {'libraries':[('boost_python_src',{'include_dirs':[src_dir,py_incl_dir],
                                                  'sources':bpl_srcs})],
                'include_dirs':[src_dir],
                }
        if info:
            self.set_info(**info)
        return

class agg2_info(system_info):
    section = 'agg2'
    dir_env_var = 'AGG2'

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend([d] + self.combine_paths(d,['agg2*']))
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        src_dirs = self.get_src_dirs()
        src_dir = ''
        for d in src_dirs:
            if os.path.isfile(os.path.join(d,'src','agg_affine_matrix.cpp')):
                src_dir = d
                break
        if not src_dir:
            return
        if sys.platform=='win32':
            agg2_srcs = glob(os.path.join(src_dir,'src','platform','win32','agg_win32_bmp.cpp'))
        else:
            agg2_srcs = glob(os.path.join(src_dir,'src','*.cpp'))
            agg2_srcs += [os.path.join(src_dir,'src','platform','X11','agg_platform_support.cpp')]

        info = {'libraries':[('agg2_src',{'sources':agg2_srcs,
                                          'include_dirs':[os.path.join(src_dir,'include')],
                                          })],
                'include_dirs':[os.path.join(src_dir,'include')],
                }
        if info:
            self.set_info(**info)
        return

class _pkg_config_info(system_info):
    section = None
    config_env_var = 'PKG_CONFIG'
    default_config_exe = 'pkg-config'
    append_config_exe = ''
    version_macro_name = None
    release_macro_name = None
    version_flag = '--modversion'
    cflags_flag = '--cflags'

    def get_config_exe(self):
        if os.environ.has_key(self.config_env_var):
            return os.environ[self.config_env_var]
        return self.default_config_exe
    def get_config_output(self, config_exe, option):
        s,o = exec_command(config_exe+' '+self.append_config_exe+' '+option,use_tee=0)
        if not s:
            return o

    def calc_info(self):
        config_exe = find_executable(self.get_config_exe())
        if not os.path.isfile(config_exe):
            log.warn('File not found: %s. Cannot determine %s info.' \
                  % (config_exe, self.section))
            return
        info = {}
        macros = []
        libraries = []
        library_dirs = []
        include_dirs = []
        extra_link_args = []
        extra_compile_args = []
        version = self.get_config_output(config_exe,self.version_flag)
        if version:
            macros.append((self.__class__.__name__.split('.')[-1].upper(),
                           '"\\"%s\\""' % (version)))
            if self.version_macro_name:
                macros.append((self.version_macro_name+'_%s' % (version.replace('.','_')),None))
        if self.release_macro_name:
            release = self.get_config_output(config_exe,'--release')
            if release:
                macros.append((self.release_macro_name+'_%s' % (release.replace('.','_')),None))
        opts = self.get_config_output(config_exe,'--libs')
        if opts:
            for opt in opts.split():
                if opt[:2]=='-l':
                    libraries.append(opt[2:])
                elif opt[:2]=='-L':
                    library_dirs.append(opt[2:])
                else:
                    extra_link_args.append(opt)
        opts = self.get_config_output(config_exe,self.cflags_flag)
        if opts:
            for opt in opts.split():
                if opt[:2]=='-I':
                    include_dirs.append(opt[2:])
                elif opt[:2]=='-D':
                    if '=' in opt:
                        n,v = opt[2:].split('=')
                        macros.append((n,v))
                    else:
                        macros.append((opt[2:],None))
                else:
                    extra_compile_args.append(opt)
        if macros: dict_append(info, define_macros = macros)
        if libraries: dict_append(info, libraries = libraries)
        if library_dirs: dict_append(info, library_dirs = library_dirs)
        if include_dirs: dict_append(info, include_dirs = include_dirs)
        if extra_link_args: dict_append(info, extra_link_args = extra_link_args)
        if extra_compile_args: dict_append(info, extra_compile_args = extra_compile_args)
        if info:
            self.set_info(**info)
        return

class wx_info(_pkg_config_info):
    section = 'wx'
    config_env_var = 'WX_CONFIG'
    default_config_exe = 'wx-config'
    append_config_exe = ''
    version_macro_name = 'WX_VERSION'
    release_macro_name = 'WX_RELEASE'
    version_flag = '--version'
    cflags_flag = '--cxxflags'

class gdk_pixbuf_xlib_2_info(_pkg_config_info):
    section = 'gdk_pixbuf_xlib_2'
    append_config_exe = 'gdk-pixbuf-xlib-2.0'
    version_macro_name = 'GDK_PIXBUF_XLIB_VERSION'

class gdk_pixbuf_2_info(_pkg_config_info):
    section = 'gdk_pixbuf_2'
    append_config_exe = 'gdk-pixbuf-2.0'
    version_macro_name = 'GDK_PIXBUF_VERSION'

class gdk_x11_2_info(_pkg_config_info):
    section = 'gdk_x11_2'
    append_config_exe = 'gdk-x11-2.0'
    version_macro_name = 'GDK_X11_VERSION'

class gdk_2_info(_pkg_config_info):
    section = 'gdk_2'
    append_config_exe = 'gdk-2.0'
    version_macro_name = 'GDK_VERSION'

class gdk_info(_pkg_config_info):
    section = 'gdk'
    append_config_exe = 'gdk'
    version_macro_name = 'GDK_VERSION'

class gtkp_x11_2_info(_pkg_config_info):
    section = 'gtkp_x11_2'
    append_config_exe = 'gtk+-x11-2.0'
    version_macro_name = 'GTK_X11_VERSION'


class gtkp_2_info(_pkg_config_info):
    section = 'gtkp_2'
    append_config_exe = 'gtk+-2.0'
    version_macro_name = 'GTK_VERSION'

class xft_info(_pkg_config_info):
    section = 'xft'
    append_config_exe = 'xft'
    version_macro_name = 'XFT_VERSION'

class freetype2_info(_pkg_config_info):
    section = 'freetype2'
    append_config_exe = 'freetype2'
    version_macro_name = 'FREETYPE2_VERSION'

class amd_info(system_info):
    section = 'amd'
    dir_env_var = 'AMD'
    _lib_names = ['amd']

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()

        amd_libs = self.get_libs('amd_libs', self._lib_names)
        for d in lib_dirs:
            amd = self.check_libs(d,amd_libs,[])
            if amd is not None:
                info = amd
                break
        else:
            return

        include_dirs = self.get_include_dirs()

        inc_dir = None
        for d in include_dirs:
            p = self.combine_paths(d,'amd.h')
            if p:
                inc_dir = os.path.dirname(p[0])
                break
        if inc_dir is not None:
            dict_append(info, include_dirs=[inc_dir],
                        define_macros=[('SCIPY_AMD_H',None)],
                        swig_opts = ['-I' + inc_dir])

        self.set_info(**info)
        return

class umfpack_info(system_info):
    section = 'umfpack'
    dir_env_var = 'UMFPACK'
    notfounderror = UmfpackNotFoundError
    _lib_names = ['umfpack']

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()

        umfpack_libs = self.get_libs('umfpack_libs', self._lib_names)
        for d in lib_dirs:
            umf = self.check_libs(d,umfpack_libs,[])
            if umf is not None:
                info = umf
                break
        else:
            return

        include_dirs = self.get_include_dirs()

        inc_dir = None
        for d in include_dirs:
            p = self.combine_paths(d,['','umfpack'],'umfpack.h')
            if p:
                inc_dir = os.path.dirname(p[0])
                break
        if inc_dir is not None:
            dict_append(info, include_dirs=[inc_dir],
                        define_macros=[('SCIPY_UMFPACK_H',None)],
                        swig_opts = ['-I' + inc_dir])

        amd = get_info('amd')
        dict_append(info, **get_info('amd'))

        self.set_info(**info)
        return

## def vstr2hex(version):
##     bits = []
##     n = [24,16,8,4,0]
##     r = 0
##     for s in version.split('.'):
##         r |= int(s) << n[0]
##         del n[0]
##     return r

#--------------------------------------------------------------------

def combine_paths(*args,**kws):
    """ Return a list of existing paths composed by all combinations of
        items from arguments.
    """
    r = []
    for a in args:
        if not a: continue
        if is_string(a):
            a = [a]
        r.append(a)
    args = r
    if not args: return []
    if len(args)==1:
        result = reduce(lambda a,b:a+b,map(glob,args[0]),[])
    elif len (args)==2:
        result = []
        for a0 in args[0]:
            for a1 in args[1]:
                result.extend(glob(os.path.join(a0,a1)))
    else:
        result = combine_paths(*(combine_paths(args[0],args[1])+args[2:]))
    verbosity = kws.get('verbosity',1)
    log.debug('(paths: %s)', ','.join(result))
    return result

language_map = {'c':0,'c++':1,'f77':2,'f90':3}
inv_language_map = {0:'c',1:'c++',2:'f77',3:'f90'}
def dict_append(d,**kws):
    languages = []
    for k,v in kws.items():
        if k=='language':
            languages.append(v)
            continue
        if d.has_key(k):
            if k in ['library_dirs','include_dirs','define_macros']:
                [d[k].append(vv) for vv in v if vv not in d[k]]
            else:
                d[k].extend(v)
        else:
            d[k] = v
    if languages:
        l = inv_language_map[max([language_map.get(l,0) for l in languages])]
        d['language'] = l
    return

def parseCmdLine(argv=(None,)):
    import optparse
    parser = optparse.OptionParser("usage: %prog [-v] [info objs]")
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                      default=False,
                      help='be verbose and print more messages')

    opts, args = parser.parse_args(args=argv[1:])
    return opts, args

def show_all(argv=None):
    import inspect
    if argv is None:
        argv = sys.argv
    opts, args = parseCmdLine(argv)
    if opts.verbose:
        log.set_threshold(log.DEBUG)
    else:
        log.set_threshold(log.INFO)
    show_only = []
    for n in args:
        if n[-5:] != '_info':
            n = n + '_info'
        show_only.append(n)
    show_all = not show_only
    _gdict_ = globals().copy()
    for name, c in _gdict_.iteritems():
        if not inspect.isclass(c):
            continue
        if not issubclass(c, system_info) or c is system_info:
            continue
        if not show_all:
            if name not in show_only:
                continue
            del show_only[show_only.index(name)]
        conf = c()
        conf.verbosity = 2
        r = conf.get_info()
    if show_only:
        log.info('Info classes not defined: %s',','.join(show_only))

if __name__ == "__main__":
    show_all()


from __version__ import version as __version__
# Must import local ccompiler ASAP in order to get
# customized CCompiler.spawn effective.
import ccompiler
import unixccompiler

from info import __doc__

try:
    import __config__
    _INSTALLED = True
except ImportError:
    _INSTALLED = False

if _INSTALLED:
    def test(level=1, verbosity=1):
        from numpy.testing import NumpyTest
        return NumpyTest().test(level, verbosity)


import sys
from distutils.core import *

if 'setuptools' in sys.modules:
    have_setuptools = True
    from setuptools import setup as old_setup
    # easy_install imports math, it may be picked up from cwd
    from setuptools.command import develop, easy_install
    try:
        # very old versions of setuptools don't have this
        from setuptools.command import bdist_egg
    except ImportError:
        have_setuptools = False
else:
    from distutils.core import setup as old_setup
    have_setuptools = False

import warnings
import distutils.core
import distutils.dist

from numpy.distutils.extension import Extension
from numpy.distutils.command import config
from numpy.distutils.command import build
from numpy.distutils.command import build_py
from numpy.distutils.command import config_compiler
from numpy.distutils.command import build_ext
from numpy.distutils.command import build_clib
from numpy.distutils.command import build_src
from numpy.distutils.command import build_scripts
from numpy.distutils.command import sdist
from numpy.distutils.command import install_data
from numpy.distutils.command import install_headers
from numpy.distutils.command import install
from numpy.distutils.command import bdist_rpm
from numpy.distutils.misc_util import get_data_files, is_sequence, is_string

numpy_cmdclass = {'build':            build.build,
                  'build_src':        build_src.build_src,
                  'build_scripts':    build_scripts.build_scripts,
                  'config_fc':        config_compiler.config_fc,
                  'config':           config.config,
                  'build_ext':        build_ext.build_ext,
                  'build_py':         build_py.build_py,
                  'build_clib':       build_clib.build_clib,
                  'sdist':            sdist.sdist,
                  'install_data':     install_data.install_data,
                  'install_headers':  install_headers.install_headers,
                  'install':          install.install,
                  'bdist_rpm':        bdist_rpm.bdist_rpm,
                  }
if have_setuptools:
    from numpy.distutils.command import egg_info
    numpy_cmdclass['bdist_egg'] = bdist_egg.bdist_egg
    numpy_cmdclass['develop'] = develop.develop
    numpy_cmdclass['easy_install'] = easy_install.easy_install
    numpy_cmdclass['egg_info'] = egg_info.egg_info

def _dict_append(d, **kws):
    for k,v in kws.items():
        if not d.has_key(k):
            d[k] = v
            continue
        dv = d[k]
        if isinstance(dv, tuple):
            d[k] = dv + tuple(v)
        elif isinstance(dv, list):
            d[k] = dv + list(v)
        elif isinstance(dv, dict):
            _dict_append(dv, **v)
        elif is_string(dv):
            d[k] = dv + v
        else:
            raise TypeError,`type(dv)`

def _command_line_ok(_cache=[]):
    """ Return True if command line does not contain any
    help or display requests.
    """
    if _cache:
        return _cache[0]
    ok = True
    display_opts = ['--'+n for n in Distribution.display_option_names]
    for o in Distribution.display_options:
        if o[1]:
            display_opts.append('-'+o[1])
    for arg in sys.argv:
        if arg.startswith('--help') or arg=='-h' or arg in display_opts:
            ok = False
            break
    _cache.append(ok)
    return ok

def _exit_interactive_session(_cache=[]):
    if _cache:
        return # been here
    _cache.append(1)
    print '-'*72
    raw_input('Press ENTER to close the interactive session..')
    print '='*72

def get_distribution(always=False):
    dist = distutils.core._setup_distribution
    # XXX Hack to get numpy installable with easy_install.
    # The problem is easy_install runs it's own setup(), which
    # sets up distutils.core._setup_distribution. However,
    # when our setup() runs, that gets overwritten and lost.
    # We can't use isinstance, as the DistributionWithoutHelpCommands
    # class is local to a function in setuptools.command.easy_install
    if dist is not None and \
            repr(dist).find('DistributionWithoutHelpCommands') != -1:
        dist = None
    if always and dist is None:
        dist = distutils.dist.Distribution()
    return dist

def setup(**attr):

    if len(sys.argv)<=1:
        from interactive import interactive_sys_argv
        import atexit
        atexit.register(_exit_interactive_session)
        sys.argv[:] = interactive_sys_argv(sys.argv)
        if len(sys.argv)>1:
            return setup(**attr)

    cmdclass = numpy_cmdclass.copy()

    new_attr = attr.copy()
    if new_attr.has_key('cmdclass'):
        cmdclass.update(new_attr['cmdclass'])
    new_attr['cmdclass'] = cmdclass

    if new_attr.has_key('configuration'):
        # To avoid calling configuration if there are any errors
        # or help request in command in the line.
        configuration = new_attr.pop('configuration')

        old_dist = distutils.core._setup_distribution
        old_stop = distutils.core._setup_stop_after
        distutils.core._setup_distribution = None
        distutils.core._setup_stop_after = "commandline"
        try:
            dist = setup(**new_attr)
        finally:
            distutils.core._setup_distribution = old_dist
            distutils.core._setup_stop_after = old_stop
        if dist.help or not _command_line_ok():
            # probably displayed help, skip running any commands
            return dist

        # create setup dictionary and append to new_attr
        config = configuration()
        if hasattr(config,'todict'):
            config = config.todict()
        _dict_append(new_attr, **config)

    # Move extension source libraries to libraries
    libraries = []
    for ext in new_attr.get('ext_modules',[]):
        new_libraries = []
        for item in ext.libraries:
            if is_sequence(item):
                lib_name, build_info = item
                _check_append_ext_library(libraries, item)
                new_libraries.append(lib_name)
            elif is_string(item):
                new_libraries.append(item)
            else:
                raise TypeError("invalid description of extension module "
                                "library %r" % (item,))
        ext.libraries = new_libraries
    if libraries:
        if not new_attr.has_key('libraries'):
            new_attr['libraries'] = []
        for item in libraries:
            _check_append_library(new_attr['libraries'], item)

    # sources in ext_modules or libraries may contain header files
    if (new_attr.has_key('ext_modules') or new_attr.has_key('libraries')) \
       and not new_attr.has_key('headers'):
        new_attr['headers'] = []

    return old_setup(**new_attr)

def _check_append_library(libraries, item):
    for libitem in libraries:
        if is_sequence(libitem):
            if is_sequence(item):
                if item[0]==libitem[0]:
                    if item[1] is libitem[1]:
                        return
                    warnings.warn("[0] libraries list contains %r with"
                                  " different build_info" % (item[0],))
                    break
            else:
                if item==libitem[0]:
                    warnings.warn("[1] libraries list contains %r with"
                                  " no build_info" % (item[0],))
                    break
        else:
            if is_sequence(item):
                if item[0]==libitem:
                    warnings.warn("[2] libraries list contains %r with"
                                  " no build_info" % (item[0],))
                    break
            else:
                if item==libitem:
                    return
    libraries.append(item)

def _check_append_ext_library(libraries, (lib_name,build_info)):
    for item in libraries:
        if is_sequence(item):
            if item[0]==lib_name:
                if item[1] is build_info:
                    return
                warnings.warn("[3] libraries list contains %r with"
                              " different build_info" % (lib_name,))
                break
        elif item==lib_name:
            warnings.warn("[4] libraries list contains %r with"
                          " no build_info" % (lib_name,))
            break
    libraries.append((lib_name,build_info))

major = 0
minor = 4
micro = 0
version = '%(major)d.%(minor)d.%(micro)d' % (locals())

#!/usr/bin/env python
"""
exec_command

Implements exec_command function that is (almost) equivalent to
commands.getstatusoutput function but on NT, DOS systems the
returned status is actually correct (though, the returned status
values may be different by a factor). In addition, exec_command
takes keyword arguments for (re-)defining environment variables.

Provides functions:
  exec_command  --- execute command in a specified directory and
                    in the modified environment.
  splitcmdline  --- inverse of ' '.join(argv)
  find_executable --- locate a command using info from environment
                    variable PATH. Equivalent to posix `which`
                    command.

Author: Pearu Peterson <pearu@cens.ioc.ee>
Created: 11 January 2003

Requires: Python 2.x

Succesfully tested on:
  os.name | sys.platform | comments
  --------+--------------+----------
  posix   | linux2       | Debian (sid) Linux, Python 2.1.3+, 2.2.3+, 2.3.3
                           PyCrust 0.9.3, Idle 1.0.2
  posix   | linux2       | Red Hat 9 Linux, Python 2.1.3, 2.2.2, 2.3.2
  posix   | sunos5       | SunOS 5.9, Python 2.2, 2.3.2
  posix   | darwin       | Darwin 7.2.0, Python 2.3
  nt      | win32        | Windows Me
                           Python 2.3(EE), Idle 1.0, PyCrust 0.7.2
                           Python 2.1.1 Idle 0.8
  nt      | win32        | Windows 98, Python 2.1.1. Idle 0.8
  nt      | win32        | Cygwin 98-4.10, Python 2.1.1(MSC) - echo tests
                           fail i.e. redefining environment variables may
                           not work. FIXED: don't use cygwin echo!
                           Comment: also `cmd /c echo` will not work
                           but redefining environment variables do work.
  posix   | cygwin       | Cygwin 98-4.10, Python 2.3.3(cygming special)
  nt      | win32        | Windows XP, Python 2.3.3

Known bugs:
- Tests, that send messages to stderr, fail when executed from MSYS prompt
  because the messages are lost at some point.
"""

__all__ = ['exec_command','find_executable']

import os
import re
import sys
import tempfile

from numpy.distutils.misc_util import is_sequence

############################################################

from log import _global_log as log

############################################################

def get_pythonexe():
    pythonexe = sys.executable
    if os.name in ['nt','dos']:
        fdir,fn = os.path.split(pythonexe)
        fn = fn.upper().replace('PYTHONW','PYTHON')
        pythonexe = os.path.join(fdir,fn)
        assert os.path.isfile(pythonexe), '%r is not a file' % (pythonexe,)
    return pythonexe

############################################################

def splitcmdline(line):
    """ Inverse of ' '.join(sys.argv).
    """
    log.debug('splitcmdline(%r)' % (line))
    lst = []
    flag = 0
    s,pc,cc = '','',''
    for nc in line+' ':
        if flag==0:
            flag = (pc != '\\' and \
                     ((cc=='"' and 1) or (cc=="'" and 2) or \
                       (cc==' ' and pc!=' ' and -2))) or flag
        elif flag==1:
            flag = (cc=='"' and pc!='\\' and nc==' ' and -1) or flag
        elif flag==2:
            flag = (cc=="'" and pc!='\\' and nc==' ' and -1) or flag
        if flag!=-2:
            s += cc
        if flag<0:
            flag = 0
            s = s.strip()
            if s:
                lst.append(s)
                s = ''
        pc,cc = cc,nc
    else:
        s = s.strip()
        if s:
            lst.append(s)
    log.debug('splitcmdline -> %r' % (lst))
    return lst

def test_splitcmdline():
    l = splitcmdline('a   b  cc')
    assert l==['a','b','cc'], repr(l)
    l = splitcmdline('a')
    assert l==['a'], repr(l)
    l = splitcmdline('a "  b  cc"')
    assert l==['a','"  b  cc"'], repr(l)
    l = splitcmdline('"a bcc"  -h')
    assert l==['"a bcc"','-h'], repr(l)
    l = splitcmdline(r'"\"a \" bcc" -h')
    assert l==[r'"\"a \" bcc"','-h'], repr(l)
    l = splitcmdline(" 'a bcc'  -h")
    assert l==["'a bcc'",'-h'], repr(l)
    l = splitcmdline(r"'\'a \' bcc' -h")
    assert l==[r"'\'a \' bcc'",'-h'], repr(l)

############################################################

def find_executable(exe, path=None):
    """ Return full path of a executable.
    """
    log.debug('find_executable(%r)' % exe)
    orig_exe = exe
    if path is None:
        path = os.environ.get('PATH',os.defpath)
    if os.name=='posix' and sys.version[:3]>'2.1':
        realpath = os.path.realpath
    else:
        realpath = lambda a:a
    if exe[0]=='"':
        exe = exe[1:-1]
    suffices = ['']
    if os.name in ['nt','dos','os2']:
        fn,ext = os.path.splitext(exe)
        extra_suffices = ['.exe','.com','.bat']
        if ext.lower() not in extra_suffices:
            suffices = extra_suffices
    if os.path.isabs(exe):
        paths = ['']
    else:
        paths = map(os.path.abspath, path.split(os.pathsep))
        if 0 and os.name == 'nt':
            new_paths = []
            cygwin_paths = []
            for path in paths:
                d,p = os.path.splitdrive(path)
                if p.lower().find('cygwin') >= 0:
                    cygwin_paths.append(path)
                else:
                    new_paths.append(path)
            paths = new_paths + cygwin_paths
    for path in paths:
        fn = os.path.join(path,exe)
        for s in suffices:
            f_ext = fn+s
            if not os.path.islink(f_ext):
                # see comment below.
                f_ext = realpath(f_ext)
            if os.path.isfile(f_ext) and os.access(f_ext,os.X_OK):
                log.debug('Found executable %s' % f_ext)
                return f_ext
    if os.path.islink(exe):
        # Don't follow symbolic links. E.g. when using colorgcc then
        # gcc -> /usr/bin/colorgcc
        # g77 -> /usr/bin/colorgcc
        pass
    else:
        exe = realpath(exe)
    if not os.path.isfile(exe) or os.access(exe,os.X_OK):
        log.warn('Could not locate executable %s' % orig_exe)
        return orig_exe
    return exe

############################################################

def _preserve_environment( names ):
    log.debug('_preserve_environment(%r)' % (names))
    env = {}
    for name in names:
        env[name] = os.environ.get(name)
    return env

def _update_environment( **env ):
    log.debug('_update_environment(...)')
    for name,value in env.items():
        os.environ[name] = value or ''

def exec_command( command,
                  execute_in='', use_shell=None, use_tee = None,
                  _with_python = 1,
                  **env ):
    """ Return (status,output) of executed command.

    command is a concatenated string of executable and arguments.
    The output contains both stdout and stderr messages.
    The following special keyword arguments can be used:
      use_shell - execute `sh -c command`
      use_tee   - pipe the output of command through tee
      execute_in - before command `cd execute_in` and after `cd -`.

    On NT, DOS systems the returned status is correct for external commands.
    Wild cards will not work for non-posix systems or when use_shell=0.
    """
    log.debug('exec_command(%r,%s)' % (command,\
         ','.join(['%s=%r'%kv for kv in env.items()])))

    if use_tee is None:
        use_tee = os.name=='posix'
    if use_shell is None:
        use_shell = os.name=='posix'
    execute_in = os.path.abspath(execute_in)
    oldcwd = os.path.abspath(os.getcwd())

    if __name__[-12:] == 'exec_command':
        exec_dir = os.path.dirname(os.path.abspath(__file__))
    elif os.path.isfile('exec_command.py'):
        exec_dir = os.path.abspath('.')
    else:
        exec_dir = os.path.abspath(sys.argv[0])
        if os.path.isfile(exec_dir):
            exec_dir = os.path.dirname(exec_dir)

    if oldcwd!=execute_in:
        os.chdir(execute_in)
        log.debug('New cwd: %s' % execute_in)
    else:
        log.debug('Retaining cwd: %s' % oldcwd)

    oldenv = _preserve_environment( env.keys() )
    _update_environment( **env )

    try:
        # _exec_command is robust but slow, it relies on
        # usable sys.std*.fileno() descriptors. If they
        # are bad (like in win32 Idle, PyCrust environments)
        # then _exec_command_python (even slower)
        # will be used as a last resort.
        #
        # _exec_command_posix uses os.system and is faster
        # but not on all platforms os.system will return
        # a correct status.
        if _with_python and (0 or sys.__stdout__.fileno()==-1):
            st = _exec_command_python(command,
                                      exec_command_dir = exec_dir,
                                      **env)
        elif os.name=='posix':
            st = _exec_command_posix(command,
                                     use_shell=use_shell,
                                     use_tee=use_tee,
                                     **env)
        else:
            st = _exec_command(command, use_shell=use_shell,
                               use_tee=use_tee,**env)
    finally:
        if oldcwd!=execute_in:
            os.chdir(oldcwd)
            log.debug('Restored cwd to %s' % oldcwd)
        _update_environment(**oldenv)

    return st

def _exec_command_posix( command,
                         use_shell = None,
                         use_tee = None,
                         **env ):
    log.debug('_exec_command_posix(...)')

    if is_sequence(command):
        command_str = ' '.join(list(command))
    else:
        command_str = command

    tmpfile = tempfile.mktemp()
    stsfile = None
    if use_tee:
        stsfile = tempfile.mktemp()
        filter = ''
        if use_tee == 2:
            filter = r'| tr -cd "\n" | tr "\n" "."; echo'
        command_posix = '( %s ; echo $? > %s ) 2>&1 | tee %s %s'\
                      % (command_str,stsfile,tmpfile,filter)
    else:
        stsfile = tempfile.mktemp()
        command_posix = '( %s ; echo $? > %s ) > %s 2>&1'\
                        % (command_str,stsfile,tmpfile)
        #command_posix = '( %s ) > %s 2>&1' % (command_str,tmpfile)

    log.debug('Running os.system(%r)' % (command_posix))
    status = os.system(command_posix)

    if use_tee:
        if status:
            # if command_tee fails then fall back to robust exec_command
            log.warn('_exec_command_posix failed (status=%s)' % status)
            return _exec_command(command, use_shell=use_shell, **env)

    if stsfile is not None:
        f = open(stsfile,'r')
        status_text = f.read()
        status = int(status_text)
        f.close()
        os.remove(stsfile)

    f = open(tmpfile,'r')
    text = f.read()
    f.close()
    os.remove(tmpfile)

    if text[-1:]=='\n':
        text = text[:-1]

    return status, text


def _exec_command_python(command,
                         exec_command_dir='', **env):
    log.debug('_exec_command_python(...)')

    python_exe = get_pythonexe()
    cmdfile = tempfile.mktemp()
    stsfile = tempfile.mktemp()
    outfile = tempfile.mktemp()

    f = open(cmdfile,'w')
    f.write('import os\n')
    f.write('import sys\n')
    f.write('sys.path.insert(0,%r)\n' % (exec_command_dir))
    f.write('from exec_command import exec_command\n')
    f.write('del sys.path[0]\n')
    f.write('cmd = %r\n' % command)
    f.write('os.environ = %r\n' % (os.environ))
    f.write('s,o = exec_command(cmd, _with_python=0, **%r)\n' % (env))
    f.write('f=open(%r,"w")\nf.write(str(s))\nf.close()\n' % (stsfile))
    f.write('f=open(%r,"w")\nf.write(o)\nf.close()\n' % (outfile))
    f.close()

    cmd = '%s %s' % (python_exe, cmdfile)
    status = os.system(cmd)
    if status:
        raise RuntimeError("%r failed" % (cmd,))
    os.remove(cmdfile)

    f = open(stsfile,'r')
    status = int(f.read())
    f.close()
    os.remove(stsfile)

    f = open(outfile,'r')
    text = f.read()
    f.close()
    os.remove(outfile)

    return status, text

def quote_arg(arg):
    if arg[0]!='"' and ' ' in arg:
        return '"%s"' % arg
    return arg

def _exec_command( command, use_shell=None, use_tee = None, **env ):
    log.debug('_exec_command(...)')

    if use_shell is None:
        use_shell = os.name=='posix'
    if use_tee is None:
        use_tee = os.name=='posix'

    using_command = 0
    if use_shell:
        # We use shell (unless use_shell==0) so that wildcards can be
        # used.
        sh = os.environ.get('SHELL','/bin/sh')
        if is_sequence(command):
            argv = [sh,'-c',' '.join(list(command))]
        else:
            argv = [sh,'-c',command]
    else:
        # On NT, DOS we avoid using command.com as it's exit status is
        # not related to the exit status of a command.
        if is_sequence(command):
            argv = command[:]
        else:
            argv = splitcmdline(command)

    if hasattr(os,'spawnvpe'):
        spawn_command = os.spawnvpe
    else:
        spawn_command = os.spawnve
        argv[0] = find_executable(argv[0])
        if not os.path.isfile(argv[0]):
            log.warn('Executable %s does not exist' % (argv[0]))
            if os.name in ['nt','dos']:
                # argv[0] might be internal command
                argv = [os.environ['COMSPEC'],'/C'] + argv
                using_command = 1

    # sys.__std*__ is used instead of sys.std* because environments
    # like IDLE, PyCrust, etc overwrite sys.std* commands.
    so_fileno = sys.__stdout__.fileno()
    se_fileno = sys.__stderr__.fileno()
    so_flush = sys.__stdout__.flush
    se_flush = sys.__stderr__.flush
    so_dup = os.dup(so_fileno)
    se_dup = os.dup(se_fileno)

    outfile = tempfile.mktemp()
    fout = open(outfile,'w')
    if using_command:
        errfile = tempfile.mktemp()
        ferr = open(errfile,'w')

    log.debug('Running %s(%s,%r,%r,os.environ)' \
              % (spawn_command.__name__,os.P_WAIT,argv[0],argv))

    argv0 = argv[0]
    if not using_command:
        argv[0] = quote_arg(argv0)

    so_flush()
    se_flush()
    os.dup2(fout.fileno(),so_fileno)
    if using_command:
        #XXX: disabled for now as it does not work from cmd under win32.
        #     Tests fail on msys
        os.dup2(ferr.fileno(),se_fileno)
    else:
        os.dup2(fout.fileno(),se_fileno)
    try:
        status = spawn_command(os.P_WAIT,argv0,argv,os.environ)
    except OSError,errmess:
        status = 999
        sys.stderr.write('%s: %s'%(errmess,argv[0]))

    so_flush()
    se_flush()
    os.dup2(so_dup,so_fileno)
    os.dup2(se_dup,se_fileno)

    fout.close()
    fout = open(outfile,'r')
    text = fout.read()
    fout.close()
    os.remove(outfile)

    if using_command:
        ferr.close()
        ferr = open(errfile,'r')
        errmess = ferr.read()
        ferr.close()
        os.remove(errfile)
        if errmess and not status:
            # Not sure how to handle the case where errmess
            # contains only warning messages and that should
            # not be treated as errors.
            #status = 998
            if text:
                text = text + '\n'
            #text = '%sCOMMAND %r FAILED: %s' %(text,command,errmess)
            text = text + errmess
            print errmess
    if text[-1:]=='\n':
        text = text[:-1]
    if status is None:
        status = 0

    if use_tee:
        print text

    return status, text


def test_nt(**kws):
    pythonexe = get_pythonexe()
    echo = find_executable('echo')
    using_cygwin_echo = echo != 'echo'
    if using_cygwin_echo:
        log.warn('Using cygwin echo in win32 environment is not supported')

        s,o=exec_command(pythonexe\
                         +' -c "import os;print os.environ.get(\'AAA\',\'\')"')
        assert s==0 and o=='',(s,o)

        s,o=exec_command(pythonexe\
                         +' -c "import os;print os.environ.get(\'AAA\')"',
                         AAA='Tere')
        assert s==0 and o=='Tere',(s,o)

        os.environ['BBB'] = 'Hi'
        s,o=exec_command(pythonexe\
                         +' -c "import os;print os.environ.get(\'BBB\',\'\')"')
        assert s==0 and o=='Hi',(s,o)

        s,o=exec_command(pythonexe\
                         +' -c "import os;print os.environ.get(\'BBB\',\'\')"',
                         BBB='Hey')
        assert s==0 and o=='Hey',(s,o)

        s,o=exec_command(pythonexe\
                         +' -c "import os;print os.environ.get(\'BBB\',\'\')"')
        assert s==0 and o=='Hi',(s,o)
    elif 0:
        s,o=exec_command('echo Hello')
        assert s==0 and o=='Hello',(s,o)

        s,o=exec_command('echo a%AAA%')
        assert s==0 and o=='a',(s,o)

        s,o=exec_command('echo a%AAA%',AAA='Tere')
        assert s==0 and o=='aTere',(s,o)

        os.environ['BBB'] = 'Hi'
        s,o=exec_command('echo a%BBB%')
        assert s==0 and o=='aHi',(s,o)

        s,o=exec_command('echo a%BBB%',BBB='Hey')
        assert s==0 and o=='aHey', (s,o)
        s,o=exec_command('echo a%BBB%')
        assert s==0 and o=='aHi',(s,o)

        s,o=exec_command('this_is_not_a_command')
        assert s and o!='',(s,o)

        s,o=exec_command('type not_existing_file')
        assert s and o!='',(s,o)

    s,o=exec_command('echo path=%path%')
    assert s==0 and o!='',(s,o)

    s,o=exec_command('%s -c "import sys;sys.stderr.write(sys.platform)"' \
                     % pythonexe)
    assert s==0 and o=='win32',(s,o)

    s,o=exec_command('%s -c "raise \'Ignore me.\'"' % pythonexe)
    assert s==1 and o,(s,o)

    s,o=exec_command('%s -c "import sys;sys.stderr.write(\'0\');sys.stderr.write(\'1\');sys.stderr.write(\'2\')"'\
                     % pythonexe)
    assert s==0 and o=='012',(s,o)

    s,o=exec_command('%s -c "import sys;sys.exit(15)"' % pythonexe)
    assert s==15 and o=='',(s,o)

    s,o=exec_command('%s -c "print \'Heipa\'"' % pythonexe)
    assert s==0 and o=='Heipa',(s,o)

    print 'ok'

def test_posix(**kws):
    s,o=exec_command("echo Hello",**kws)
    assert s==0 and o=='Hello',(s,o)

    s,o=exec_command('echo $AAA',**kws)
    assert s==0 and o=='',(s,o)

    s,o=exec_command('echo "$AAA"',AAA='Tere',**kws)
    assert s==0 and o=='Tere',(s,o)


    s,o=exec_command('echo "$AAA"',**kws)
    assert s==0 and o=='',(s,o)

    os.environ['BBB'] = 'Hi'
    s,o=exec_command('echo "$BBB"',**kws)
    assert s==0 and o=='Hi',(s,o)

    s,o=exec_command('echo "$BBB"',BBB='Hey',**kws)
    assert s==0 and o=='Hey',(s,o)

    s,o=exec_command('echo "$BBB"',**kws)
    assert s==0 and o=='Hi',(s,o)


    s,o=exec_command('this_is_not_a_command',**kws)
    assert s!=0 and o!='',(s,o)

    s,o=exec_command('echo path=$PATH',**kws)
    assert s==0 and o!='',(s,o)

    s,o=exec_command('python -c "import sys,os;sys.stderr.write(os.name)"',**kws)
    assert s==0 and o=='posix',(s,o)

    s,o=exec_command('python -c "raise \'Ignore me.\'"',**kws)
    assert s==1 and o,(s,o)

    s,o=exec_command('python -c "import sys;sys.stderr.write(\'0\');sys.stderr.write(\'1\');sys.stderr.write(\'2\')"',**kws)
    assert s==0 and o=='012',(s,o)

    s,o=exec_command('python -c "import sys;sys.exit(15)"',**kws)
    assert s==15 and o=='',(s,o)

    s,o=exec_command('python -c "print \'Heipa\'"',**kws)
    assert s==0 and o=='Heipa',(s,o)

    print 'ok'

def test_execute_in(**kws):
    pythonexe = get_pythonexe()
    tmpfile = tempfile.mktemp()
    fn = os.path.basename(tmpfile)
    tmpdir = os.path.dirname(tmpfile)
    f = open(tmpfile,'w')
    f.write('Hello')
    f.close()

    s,o = exec_command('%s -c "print \'Ignore the following IOError:\','\
                       'open(%r,\'r\')"' % (pythonexe,fn),**kws)
    assert s and o!='',(s,o)
    s,o = exec_command('%s -c "print open(%r,\'r\').read()"' % (pythonexe,fn),
                       execute_in = tmpdir,**kws)
    assert s==0 and o=='Hello',(s,o)
    os.remove(tmpfile)
    print 'ok'

def test_svn(**kws):
    s,o = exec_command(['svn','status'],**kws)
    assert s,(s,o)
    print 'svn ok'

def test_cl(**kws):
    if os.name=='nt':
        s,o = exec_command(['cl','/V'],**kws)
        assert s,(s,o)
        print 'cl ok'

if os.name=='posix':
    test = test_posix
elif os.name in ['nt','dos']:
    test = test_nt
else:
    raise NotImplementedError,'exec_command tests for '+os.name

############################################################

if __name__ == "__main__":

    test_splitcmdline()
    test(use_tee=0)
    test(use_tee=1)
    test_execute_in(use_tee=0)
    test_execute_in(use_tee=1)
    test_svn(use_tee=1)
    test_cl(use_tee=1)

#!/usr/bin/python
"""

process_file(filename)

  takes templated file .xxx.src and produces .xxx file where .xxx
  is .pyf .f90 or .f using the following template rules:

  '<..>' denotes a template.

  All function and subroutine blocks in a source file with names that
  contain '<..>' will be replicated according to the rules in '<..>'.

  The number of comma-separeted words in '<..>' will determine the number of
  replicates.

  '<..>' may have two different forms, named and short. For example,

  named:
   <p=d,s,z,c> where anywhere inside a block '<p>' will be replaced with
   'd', 's', 'z', and 'c' for each replicate of the block.

   <_c>  is already defined: <_c=s,d,c,z>
   <_t>  is already defined: <_t=real,double precision,complex,double complex>

  short:
   <s,d,c,z>, a short form of the named, useful when no <p> appears inside
   a block.

  In general, '<..>' contains a comma separated list of arbitrary
  expressions. If these expression must contain a comma|leftarrow|rightarrow,
  then prepend the comma|leftarrow|rightarrow with a backslash.

  If an expression matches '\\<index>' then it will be replaced
  by <index>-th expression.

  Note that all '<..>' forms in a block must have the same number of
  comma-separated entries.

 Predefined named template rules:
  <prefix=s,d,c,z>
  <ftype=real,double precision,complex,double complex>
  <ftypereal=real,double precision,\\0,\\1>
  <ctype=float,double,complex_float,complex_double>
  <ctypereal=float,double,\\0,\\1>

"""

__all__ = ['process_str','process_file']

import os
import sys
import re

routine_start_re = re.compile(r'(\n|\A)((     (\$|\*))|)\s*(subroutine|function)\b',re.I)
routine_end_re = re.compile(r'\n\s*end\s*(subroutine|function)\b.*(\n|\Z)',re.I)
function_start_re = re.compile(r'\n     (\$|\*)\s*function\b',re.I)

def parse_structure(astr):
    """ Return a list of tuples for each function or subroutine each
    tuple is the start and end of a subroutine or function to be
    expanded.
    """

    spanlist = []
    ind = 0
    while 1:
        m = routine_start_re.search(astr,ind)
        if m is None:
            break
        start = m.start()
        if function_start_re.match(astr,start,m.end()):
            while 1:
                i = astr.rfind('\n',ind,start)
                if i==-1:
                    break
                start = i
                if astr[i:i+7]!='\n     $':
                    break
        start += 1
        m = routine_end_re.search(astr,m.end())
        ind = end = m and m.end()-1 or len(astr)
        spanlist.append((start,end))
    return spanlist

template_re = re.compile(r"<\s*(\w[\w\d]*)\s*>")
named_re = re.compile(r"<\s*(\w[\w\d]*)\s*=\s*(.*?)\s*>")
list_re = re.compile(r"<\s*((.*?))\s*>")

def find_repl_patterns(astr):
    reps = named_re.findall(astr)
    names = {}
    for rep in reps:
        name = rep[0].strip() or unique_key(names)
        repl = rep[1].replace('\,','@comma@')
        thelist = conv(repl)
        names[name] = thelist
    return names

item_re = re.compile(r"\A\\(?P<index>\d+)\Z")
def conv(astr):
    b = astr.split(',')
    l = [x.strip() for x in b]
    for i in range(len(l)):
        m = item_re.match(l[i])
        if m:
            j = int(m.group('index'))
            l[i] = l[j]
    return ','.join(l)

def unique_key(adict):
    """ Obtain a unique key given a dictionary."""
    allkeys = adict.keys()
    done = False
    n = 1
    while not done:
        newkey = '__l%s' % (n)
        if newkey in allkeys:
            n += 1
        else:
            done = True
    return newkey


template_name_re = re.compile(r'\A\s*(\w[\w\d]*)\s*\Z')
def expand_sub(substr,names):
    substr = substr.replace('\>','@rightarrow@')
    substr = substr.replace('\<','@leftarrow@')
    lnames = find_repl_patterns(substr)
    substr = named_re.sub(r"<\1>",substr)  # get rid of definition templates

    def listrepl(mobj):
        thelist = conv(mobj.group(1).replace('\,','@comma@'))
        if template_name_re.match(thelist):
            return "<%s>" % (thelist)
        name = None
        for key in lnames.keys():    # see if list is already in dictionary
            if lnames[key] == thelist:
                name = key
        if name is None:      # this list is not in the dictionary yet
            name = unique_key(lnames)
            lnames[name] = thelist
        return "<%s>" % name

    substr = list_re.sub(listrepl, substr) # convert all lists to named templates
                                           # newnames are constructed as needed

    numsubs = None
    base_rule = None
    rules = {}
    for r in template_re.findall(substr):
        if not rules.has_key(r):
            thelist = lnames.get(r,names.get(r,None))
            if thelist is None:
                raise ValueError,'No replicates found for <%s>' % (r)
            if not names.has_key(r) and not thelist.startswith('_'):
                names[r] = thelist
            rule = [i.replace('@comma@',',') for i in thelist.split(',')]
            num = len(rule)

            if numsubs is None:
                numsubs = num
                rules[r] = rule
                base_rule = r
            elif num == numsubs:
                rules[r] = rule
            else:
                print "Mismatch in number of replacements (base <%s=%s>)"\
                      " for <%s=%s>. Ignoring." % (base_rule,
                                                  ','.join(rules[base_rule]),
                                                  r,thelist)
    if not rules:
        return substr

    def namerepl(mobj):
        name = mobj.group(1)
        return rules.get(name,(k+1)*[name])[k]

    newstr = ''
    for k in range(numsubs):
        newstr += template_re.sub(namerepl, substr) + '\n\n'

    newstr = newstr.replace('@rightarrow@','>')
    newstr = newstr.replace('@leftarrow@','<')
    return newstr

def process_str(allstr):
    newstr = allstr
    writestr = '' #_head # using _head will break free-format files

    struct = parse_structure(newstr)

    oldend = 0
    names = {}
    names.update(_special_names)
    for sub in struct:
        writestr += newstr[oldend:sub[0]]
        names.update(find_repl_patterns(newstr[oldend:sub[0]]))
        writestr += expand_sub(newstr[sub[0]:sub[1]],names)
        oldend =  sub[1]
    writestr += newstr[oldend:]

    return writestr

include_src_re = re.compile(r"(\n|\A)\s*include\s*['\"](?P<name>[\w\d./\\]+[.]src)['\"]",re.I)

def resolve_includes(source):
    d = os.path.dirname(source)
    fid = open(source)
    lines = []
    for line in fid.readlines():
        m = include_src_re.match(line)
        if m:
            fn = m.group('name')
            if not os.path.isabs(fn):
                fn = os.path.join(d,fn)
            if os.path.isfile(fn):
                print 'Including file',fn
                lines.extend(resolve_includes(fn))
            else:
                lines.append(line)
        else:
            lines.append(line)
    fid.close()
    return lines

def process_file(source):
    lines = resolve_includes(source)
    return process_str(''.join(lines))

_special_names = find_repl_patterns('''
<_c=s,d,c,z>
<_t=real,double precision,complex,double complex>
<prefix=s,d,c,z>
<ftype=real,double precision,complex,double complex>
<ctype=float,double,complex_float,complex_double>
<ftypereal=real,double precision,\\0,\\1>
<ctypereal=float,double,\\0,\\1>
''')

if __name__ == "__main__":

    try:
        file = sys.argv[1]
    except IndexError:
        fid = sys.stdin
        outfile = sys.stdout
    else:
        fid = open(file,'r')
        (base, ext) = os.path.splitext(file)
        newname = base
        outfile = open(newname,'w')

    allstr = fid.read()
    writestr = process_str(allstr)
    outfile.write(writestr)

"""
Support code for building Python extensions on Windows.

    # NT stuff
    # 1. Make sure libpython<version>.a exists for gcc.  If not, build it.
    # 2. Force windows to use gcc (we're struggling with MSVC and g77 support)
    # 3. Force windows to use g77

"""

import os
import sys
import log

# Overwrite certain distutils.ccompiler functions:
import numpy.distutils.ccompiler

# NT stuff
# 1. Make sure libpython<version>.a exists for gcc.  If not, build it.
# 2. Force windows to use gcc (we're struggling with MSVC and g77 support)
#    --> this is done in numpy/distutils/ccompiler.py
# 3. Force windows to use g77

import distutils.cygwinccompiler
from distutils.version import StrictVersion
from numpy.distutils.ccompiler import gen_preprocess_options, gen_lib_options
from distutils.errors import DistutilsExecError, CompileError, UnknownFileError

from distutils.unixccompiler import UnixCCompiler
from numpy.distutils.misc_util import msvc_runtime_library

# the same as cygwin plus some additional parameters
class Mingw32CCompiler(distutils.cygwinccompiler.CygwinCCompiler):
    """ A modified MingW32 compiler compatible with an MSVC built Python.

    """

    compiler_type = 'mingw32'

    def __init__ (self,
                  verbose=0,
                  dry_run=0,
                  force=0):

        distutils.cygwinccompiler.CygwinCCompiler.__init__ (self,
                                                       verbose,dry_run, force)

        # we need to support 3.2 which doesn't match the standard
        # get_versions methods regex
        if self.gcc_version is None:
            import re
            out = os.popen('gcc -dumpversion','r')
            out_string = out.read()
            out.close()
            result = re.search('(\d+\.\d+)',out_string)
            if result:
                self.gcc_version = StrictVersion(result.group(1))

        # A real mingw32 doesn't need to specify a different entry point,
        # but cygwin 2.91.57 in no-cygwin-mode needs it.
        if self.gcc_version <= "2.91.57":
            entry_point = '--entry _DllMain@12'
        else:
            entry_point = ''

        if self.linker_dll == 'dllwrap':
            # Commented out '--driver-name g++' part that fixes weird
            #   g++.exe: g++: No such file or directory
            # error (mingw 1.0 in Enthon24 tree, gcc-3.4.5).
            # If the --driver-name part is required for some environment
            # then make the inclusion of this part specific to that environment.
            self.linker = 'dllwrap' #  --driver-name g++'
        elif self.linker_dll == 'gcc':
            self.linker = 'g++'

        # **changes: eric jones 4/11/01
        # 1. Check for import library on Windows.  Build if it doesn't exist.

        build_import_library()

        # **changes: eric jones 4/11/01
        # 2. increased optimization and turned off all warnings
        # 3. also added --driver-name g++
        #self.set_executables(compiler='gcc -mno-cygwin -O2 -w',
        #                     compiler_so='gcc -mno-cygwin -mdll -O2 -w',
        #                     linker_exe='gcc -mno-cygwin',
        #                     linker_so='%s --driver-name g++ -mno-cygwin -mdll -static %s'
        #                                % (self.linker, entry_point))
        if self.gcc_version <= "3.0.0":
            self.set_executables(compiler='gcc -mno-cygwin -O2 -w',
                                 compiler_so='gcc -mno-cygwin -mdll -O2 -w -Wstrict-prototypes',
                                 linker_exe='g++ -mno-cygwin',
                                 linker_so='%s -mno-cygwin -mdll -static %s'
                                 % (self.linker, entry_point))
        else:
            self.set_executables(compiler='gcc -mno-cygwin -O2 -Wall',
                                 compiler_so='gcc -mno-cygwin -O2 -Wall -Wstrict-prototypes',
                                 linker_exe='g++ -mno-cygwin',
                                 linker_so='g++ -mno-cygwin -shared')
        # added for python2.3 support
        # we can't pass it through set_executables because pre 2.2 would fail
        self.compiler_cxx = ['g++']

        # Maybe we should also append -mthreads, but then the finished
        # dlls need another dll (mingwm10.dll see Mingw32 docs)
        # (-mthreads: Support thread-safe exception handling on `Mingw32')

        # no additional libraries needed
        #self.dll_libraries=[]
        return

    # __init__ ()

    def link(self,
             target_desc,
             objects,
             output_filename,
             output_dir,
             libraries,
             library_dirs,
             runtime_library_dirs,
             export_symbols = None,
             debug=0,
             extra_preargs=None,
             extra_postargs=None,
             build_temp=None,
             target_lang=None):
        # Include the appropiate MSVC runtime library if Python was built
        # with MSVC >= 7.0 (MinGW standard is msvcrt)
        runtime_library = msvc_runtime_library()
        if runtime_library:
            if not libraries:
                libraries = []
            libraries.append(runtime_library)
        args = (self,
                target_desc,
                objects,
                output_filename,
                output_dir,
                libraries,
                library_dirs,
                runtime_library_dirs,
                None, #export_symbols, we do this in our def-file
                debug,
                extra_preargs,
                extra_postargs,
                build_temp,
                target_lang)
        if self.gcc_version < "3.0.0":
            func = distutils.cygwinccompiler.CygwinCCompiler.link
        else:
            func = UnixCCompiler.link
        func(*args[:func.im_func.func_code.co_argcount])
        return

    def object_filenames (self,
                          source_filenames,
                          strip_dir=0,
                          output_dir=''):
        if output_dir is None: output_dir = ''
        obj_names = []
        for src_name in source_filenames:
            # use normcase to make sure '.rc' is really '.rc' and not '.RC'
            (base, ext) = os.path.splitext (os.path.normcase(src_name))

            # added these lines to strip off windows drive letters
            # without it, .o files are placed next to .c files
            # instead of the build directory
            drv,base = os.path.splitdrive(base)
            if drv:
                base = base[1:]

            if ext not in (self.src_extensions + ['.rc','.res']):
                raise UnknownFileError, \
                      "unknown file type '%s' (from '%s')" % \
                      (ext, src_name)
            if strip_dir:
                base = os.path.basename (base)
            if ext == '.res' or ext == '.rc':
                # these need to be compiled to object files
                obj_names.append (os.path.join (output_dir,
                                                base + ext + self.obj_extension))
            else:
                obj_names.append (os.path.join (output_dir,
                                                base + self.obj_extension))
        return obj_names

    # object_filenames ()


def build_import_library():
    """ Build the import libraries for Mingw32-gcc on Windows
    """
    if os.name != 'nt':
        return
    lib_name = "python%d%d.lib" % tuple(sys.version_info[:2])
    lib_file = os.path.join(sys.prefix,'libs',lib_name)
    out_name = "libpython%d%d.a" % tuple(sys.version_info[:2])
    out_file = os.path.join(sys.prefix,'libs',out_name)
    if not os.path.isfile(lib_file):
        log.warn('Cannot build import library: "%s" not found' % (lib_file))
        return
    if os.path.isfile(out_file):
        log.debug('Skip building import library: "%s" exists' % (out_file))
        return
    log.info('Building import library: "%s"' % (out_file))

    from numpy.distutils import lib2def

    def_name = "python%d%d.def" % tuple(sys.version_info[:2])
    def_file = os.path.join(sys.prefix,'libs',def_name)
    nm_cmd = '%s %s' % (lib2def.DEFAULT_NM, lib_file)
    nm_output = lib2def.getnm(nm_cmd)
    dlist, flist = lib2def.parse_nm(nm_output)
    lib2def.output_def(dlist, flist, lib2def.DEF_HEADER, open(def_file, 'w'))

    dll_name = "python%d%d.dll" % tuple(sys.version_info[:2])
    args = (dll_name,def_file,out_file)
    cmd = 'dlltool --dllname %s --def %s --output-lib %s' % args
    status = os.system(cmd)
    # for now, fail silently
    if status:
        log.warn('Failed to build import library for gcc. Linking will fail.')
    #if not success:
    #    msg = "Couldn't find import library, and failed to build it."
    #    raise DistutilsPlatformError, msg
    return

#!/usr/bin/env python

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('distutils',parent_package,top_path)
    config.add_subpackage('command')
    config.add_subpackage('fcompiler')
    config.add_data_dir('tests')
    config.add_data_files('site.cfg')
    config.make_config_py()
    return config

if __name__ == '__main__':
    from numpy.distutils.core      import setup
    setup(**configuration(top_path='').todict())

"""distutils.extension

Provides the Extension class, used to describe C/C++ extension
modules in setup scripts.

Overridden to support f2py.
"""

__revision__ = "$Id: extension.py,v 1.1 2005/04/09 19:29:34 pearu Exp $"

from distutils.extension import Extension as old_Extension

import re
cxx_ext_re = re.compile(r'.*[.](cpp|cxx|cc)\Z',re.I).match
fortran_pyf_ext_re = re.compile(r'.*[.](f90|f95|f77|for|ftn|f|pyf)\Z',re.I).match

class Extension(old_Extension):
    def __init__ (self, name, sources,
                  include_dirs=None,
                  define_macros=None,
                  undef_macros=None,
                  library_dirs=None,
                  libraries=None,
                  runtime_library_dirs=None,
                  extra_objects=None,
                  extra_compile_args=None,
                  extra_link_args=None,
                  export_symbols=None,
                  swig_opts=None,
                  depends=None,
                  language=None,
                  f2py_options=None,
                  module_dirs=None,
                 ):
        old_Extension.__init__(self,name, [],
                               include_dirs,
                               define_macros,
                               undef_macros,
                               library_dirs,
                               libraries,
                               runtime_library_dirs,
                               extra_objects,
                               extra_compile_args,
                               extra_link_args,
                               export_symbols)
        # Avoid assert statements checking that sources contains strings:
        self.sources = sources

        # Python 2.4 distutils new features
        self.swig_opts = swig_opts or []

        # Python 2.3 distutils new features
        self.depends = depends or []
        self.language = language

        # numpy_distutils features
        self.f2py_options = f2py_options or []
        self.module_dirs = module_dirs or []

        return

    def has_cxx_sources(self):
        for source in self.sources:
            if cxx_ext_re(str(source)):
                return True
        return False

    def has_f2py_sources(self):
        for source in self.sources:
            if fortran_pyf_ext_re(source):
                return True
        return False

# class Extension


import os
import sys
from pprint import pformat

__all__ = ['interactive_sys_argv']

def show_information(*args):
    print 'Python',sys.version
    for a in ['platform','prefix','byteorder','path']:
        print 'sys.%s = %s' % (a,pformat(getattr(sys,a)))
    for a in ['name']:
        print 'os.%s = %s' % (a,pformat(getattr(os,a)))
    if hasattr(os,'uname'):
        print 'system,node,release,version,machine = ',os.uname()    

def show_environ(*args):
    for k,i in os.environ.items():
        print '  %s = %s' % (k, i)

def show_fortran_compilers(*args):
    from fcompiler import show_fcompilers
    show_fcompilers({})

def show_compilers(*args):
    from distutils.ccompiler import show_compilers
    show_compilers()

def show_tasks(argv,ccompiler,fcompiler):
    print """\

Tasks: 
  i       - Show python/platform/machine information
  ie      - Show environment information
  c       - Show C compilers information
  c<name> - Set C compiler (current:%s)
  f       - Show Fortran compilers information
  f<name> - Set Fortran compiler (current:%s)
  e       - Edit proposed sys.argv[1:].

Task aliases:
  0         - Configure
  1         - Build
  2         - Install
  2<prefix> - Install with prefix.
  3         - Inplace build
  4         - Source distribution
  5         - Binary distribution

Proposed sys.argv = %s
    """ % (ccompiler, fcompiler, argv)


from exec_command import splitcmdline

def edit_argv(*args):
    argv = args[0]
    readline = args[1]
    if readline is not None:
        readline.add_history(' '.join(argv[1:]))
    try:
        s = raw_input('Edit argv [UpArrow to retrive %r]: ' % (' '.join(argv[1:])))
    except EOFError:
        return
    if s:
        argv[1:] = splitcmdline(s)
    return
    
def interactive_sys_argv(argv):
    print '='*72
    print 'Starting interactive session'
    print '-'*72

    readline = None
    try:
        try:
            import readline
        except ImportError:
            pass
        else:
            import tempfile
            tdir = tempfile.gettempdir()
            username = os.environ.get('USER',os.environ.get('USERNAME','UNKNOWN'))
            histfile = os.path.join(tdir,".pyhist_interactive_setup-" + username)
            try:
                try: readline.read_history_file(histfile)
                except IOError: pass
                import atexit
                atexit.register(readline.write_history_file, histfile)
            except AttributeError: pass
    except Exception, msg:
        print msg

    task_dict = {'i':show_information,
                 'ie':show_environ,
                 'f':show_fortran_compilers,
                 'c':show_compilers,
                 'e':edit_argv,
                 }
    c_compiler_name = None
    f_compiler_name = None

    while 1:
        show_tasks(argv,c_compiler_name, f_compiler_name)
        try:
            task = raw_input('Choose a task (^D to quit, Enter to continue with setup): ').lower()
        except EOFError:
            print
            task = 'quit'
        if task=='': break
        if task=='quit': sys.exit()
        task_func = task_dict.get(task,None)
        if task_func is None:
            if task[0]=='c':
                c_compiler_name = task[1:]
                if c_compiler_name=='none':
                    c_compiler_name = None
                continue
            if task[0]=='f':
                f_compiler_name = task[1:]
                if f_compiler_name=='none':
                    f_compiler_name = None
                continue
            if task[0]=='2' and len(task)>1:
                prefix = task[1:]
                task = task[0]
            else:
                prefix = None
            if task == '4':
                argv[1:] = ['sdist','-f']
                continue
            elif task in '01235':
                cmd_opts = {'config':[],'config_fc':[],
                            'build_ext':[],'build_src':[],
                            'build_clib':[]}
                if c_compiler_name is not None:
                    c = '--compiler=%s' % (c_compiler_name)
                    cmd_opts['config'].append(c)
                    if task != '0':
                        cmd_opts['build_ext'].append(c)
                        cmd_opts['build_clib'].append(c)
                if f_compiler_name is not None:
                    c = '--fcompiler=%s' % (f_compiler_name)
                    cmd_opts['config_fc'].append(c)
                    if task != '0':
                        cmd_opts['build_ext'].append(c)
                        cmd_opts['build_clib'].append(c)
                if task=='3':
                    cmd_opts['build_ext'].append('--inplace')
                    cmd_opts['build_src'].append('--inplace')
                conf = []
                sorted_keys = ['config','config_fc','build_src',
                               'build_clib','build_ext']
                for k in sorted_keys:
                    opts = cmd_opts[k]
                    if opts: conf.extend([k]+opts)
                if task=='0':
                    if 'config' not in conf:
                        conf.append('config')
                    argv[1:] = conf
                elif task=='1':
                    argv[1:] = conf+['build']
                elif task=='2':
                    if prefix is not None:
                        argv[1:] = conf+['install','--prefix=%s' % (prefix)]
                    else:
                        argv[1:] = conf+['install']
                elif task=='3':
                    argv[1:] = conf+['build']
                elif task=='5':
                    if sys.platform=='win32':
                        argv[1:] = conf+['bdist_wininst']
                    else:
                        argv[1:] = conf+['bdist']
            else:
                print 'Skipping unknown task:',`task`
        else:
            print '-'*68
            try:
                task_func(argv,readline)
            except Exception,msg:
                print 'Failed running task %s: %s' % (task,msg)
                break
            print '-'*68
        print

    print '-'*72
    return argv



import os
from distutils.unixccompiler import UnixCCompiler
from numpy.distutils.exec_command import find_executable

class IntelCCompiler(UnixCCompiler):

    """ A modified Intel compiler compatible with an gcc built Python.
    """

    compiler_type = 'intel'
    cc_exe = 'icc'

    def __init__ (self, verbose=0, dry_run=0, force=0):
        UnixCCompiler.__init__ (self, verbose,dry_run, force)
        compiler = self.cc_exe
        self.set_executables(compiler=compiler,
                             compiler_so=compiler,
                             compiler_cxx=compiler,
                             linker_exe=compiler,
                             linker_so=compiler + ' -shared')

class IntelItaniumCCompiler(IntelCCompiler):
    compiler_type = 'intele'

    # On Itanium, the Intel Compiler used to be called ecc, let's search for
    # it (now it's also icc, so ecc is last in the search).
    for cc_exe in map(find_executable,['icc','ecc']):
        if os.path.isfile(cc_exe):
            break

"""
Enhanced distutils with Fortran compilers support and more.
"""

postpone_import = True

#!/usr/bin/env python
def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('testnumpydistutils',parent_package,top_path)
    config.add_subpackage('pyrex_ext')
    config.add_subpackage('f2py_ext')
    #config.add_subpackage('f2py_f90_ext')
    config.add_subpackage('swig_ext')
    config.add_subpackage('gen_ext')
    return config

if __name__ == "__main__":
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())


#!/usr/bin/env python

fib3_f = '''
C FILE: FIB3.F
      SUBROUTINE FIB(A,N)
C
C     CALCULATE FIRST N FIBONACCI NUMBERS
C
      INTEGER N
      REAL*8 A(N)
Cf2py intent(in) n
Cf2py intent(out) a
Cf2py depend(n) a
      DO I=1,N
         IF (I.EQ.1) THEN
            A(I) = 0.0D0
         ELSEIF (I.EQ.2) THEN
            A(I) = 1.0D0
         ELSE
            A(I) = A(I-1) + A(I-2)
         ENDIF
      ENDDO
      END
C END FILE FIB3.F
'''

def source_func(ext, build_dir):
    import os
    from distutils.dep_util import newer
    target = os.path.join(build_dir,'fib3.f')
    if newer(__file__, target):
        f = open(target,'w')
        f.write(fib3_f)
        f.close()
    return [target]

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('gen_ext',parent_package,top_path)
    config.add_extension('fib3',
                         [source_func]
                         )
    return config

if __name__ == "__main__":
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())


#!/usr/bin/env python
def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('pyrex_ext',parent_package,top_path)
    config.add_extension('primes',
                         ['primes.pyx'])
    config.add_data_dir('tests')
    return config

if __name__ == "__main__":
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())


#!/usr/bin/env python
def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('f2py_f90_ext',parent_package,top_path)
    config.add_extension('foo',
                         ['src/foo_free.f90'],
                         include_dirs=['include'],
                         f2py_options=['--include_paths',
                                       config.paths('include')[0]]
                         )
    config.add_data_dir('tests')
    return config

if __name__ == "__main__":
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())


#!/usr/bin/env python
def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('f2py_ext',parent_package,top_path)
    config.add_extension('fib2', ['src/fib2.pyf','src/fib1.f'])
    config.add_data_dir('tests')
    return config

if __name__ == "__main__":
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())


#!/usr/bin/env python
def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('swig_ext',parent_package,top_path)
    config.add_extension('_example',
                         ['src/example.i','src/example.c']
                         )
    config.add_extension('_example2',
                         ['src/zoo.i','src/zoo.cc'],
                         depends=['src/zoo.h'],
                         include_dirs=['src']
                         )
    config.add_data_dir('tests')
    return config

if __name__ == "__main__":
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())


import re
import os
import sys
import warnings

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.ccompiler import simple_version_match
from numpy.distutils.fcompiler import FCompiler
from numpy.distutils.exec_command import exec_command, find_executable
from numpy.distutils.misc_util import mingw32, msvc_runtime_library

class GnuFCompiler(FCompiler):

    compiler_type = 'gnu'
    version_match = simple_version_match(start=r'GNU Fortran (?!95)')

    # 'g77 --version' results
    # SunOS: GNU Fortran (GCC 3.2) 3.2 20020814 (release)
    # Debian: GNU Fortran (GCC) 3.3.3 20040110 (prerelease) (Debian)
    #         GNU Fortran (GCC) 3.3.3 (Debian 20040401)
    #         GNU Fortran 0.5.25 20010319 (prerelease)
    # Redhat: GNU Fortran (GCC 3.2.2 20030222 (Red Hat Linux 3.2.2-5)) 3.2.2 20030222 (Red Hat Linux 3.2.2-5)

    for fc_exe in map(find_executable,['g77','f77']):
        if os.path.isfile(fc_exe):
            break
    executables = {
        'version_cmd'  : [fc_exe,"--version"],
        'compiler_f77' : [fc_exe, "-g", "-Wall","-fno-second-underscore"],
        'compiler_f90' : None,
        'compiler_fix' : None,
        'linker_so'    : [fc_exe, "-g", "-Wall"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"],
        'linker_exe'   : [fc_exe, "-g", "-Wall"]
        }
    module_dir_switch = None
    module_include_switch = None

    # Cygwin: f771: warning: -fPIC ignored for target (all code is
    # position independent)
    if os.name != 'nt' and sys.platform!='cygwin':
        pic_flags = ['-fPIC']

    # use -mno-cygwin for g77 when Python is not Cygwin-Python
    if sys.platform == 'win32':
        for key in ['version_cmd', 'compiler_f77', 'linker_so', 'linker_exe']:
            executables[key].append('-mno-cygwin')

    g2c = 'g2c'

    #def get_linker_so(self):
    #    # win32 linking should be handled by standard linker
    #    # Darwin g77 cannot be used as a linker.
    #    #if re.match(r'(darwin)', sys.platform):
    #    #    return
    #    return FCompiler.get_linker_so(self)

    def get_flags_linker_so(self):
        opt = self.linker_so[1:]
        if sys.platform=='darwin':
            target = os.environ.get('MACOSX_DEPLOYMENT_TARGET', None)
            if target is None:
                target = '10.3'
            major, minor = target.split('.')
            if int(minor) < 3:
                minor = '3'
                warnings.warn('Environment variable '
                    'MACOSX_DEPLOYMENT_TARGET reset to 10.3')
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = '%s.%s' % (major,
                minor)

            opt.extend(['-undefined', 'dynamic_lookup', '-bundle'])
        else:
            opt.append("-shared")
        if sys.platform[:5]=='sunos':
            # SunOS often has dynamically loaded symbols defined in the
            # static library libg2c.a  The linker doesn't like this.  To
            # ignore the problem, use the -mimpure-text flag.  It isn't
            # the safest thing, but seems to work. 'man gcc' says:
            # ".. Instead of using -mimpure-text, you should compile all
            #  source code with -fpic or -fPIC."
            opt.append('-mimpure-text')
        return opt

    def get_libgcc_dir(self):
        status, output = exec_command(self.compiler_f77 +
                                      '-print-libgcc-file-name',
                                      use_tee=0)
        if not status:
            return os.path.dirname(output)
        return None

    def get_library_dirs(self):
        opt = []
        if sys.platform[:5] != 'linux':
            d = self.get_libgcc_dir()
            if d:
                # if windows and not cygwin, libg2c lies in a different folder
                if sys.platform == 'win32' and not d.startswith('/usr/lib'):
                    d = os.path.normpath(d)
                    if not os.path.exists(os.path.join(d, 'libg2c.a')):
                        d2 = os.path.abspath(os.path.join(d,
                                                          '../../../../lib'))
                        if os.path.exists(os.path.join(d2, 'libg2c.a')):
                            opt.append(d2)
                opt.append(d)
        return opt

    def get_libraries(self):
        opt = []
        d = self.get_libgcc_dir()
        if d is not None:
            g2c = self.g2c + '-pic'
            f = self.static_lib_format % (g2c, self.static_lib_extension)
            if not os.path.isfile(os.path.join(d,f)):
                g2c = self.g2c
        else:
            g2c = self.g2c

        if g2c is not None:
            opt.append(g2c)
        if sys.platform == 'win32':
            # in case want to link F77 compiled code with MSVC
            opt.append('gcc')
            runtime_lib = msvc_runtime_library()
            if runtime_lib:
                opt.append(runtime_lib)
        if sys.platform == 'darwin':
            opt.append('cc_dynamic')
        return opt

    def get_flags_debug(self):
        return ['-g']

    def get_flags_opt(self):
        if self.get_version()<='3.3.3':
            # With this compiler version building Fortran BLAS/LAPACK
            # with -O3 caused failures in lib.lapack heevr,syevr tests.
            opt = ['-O2']
        else:
            opt = ['-O3']
        opt.append('-funroll-loops')
        return opt

    def get_flags_arch(self):
        opt = []
        if sys.platform=='darwin':
            if os.name != 'posix':
                # this should presumably correspond to Apple
                if cpu.is_ppc():
                    opt.append('-arch ppc')
                elif cpu.is_i386():
                    opt.append('-arch i386')
            for a in '601 602 603 603e 604 604e 620 630 740 7400 7450 750'\
                    '403 505 801 821 823 860'.split():
                if getattr(cpu,'is_ppc%s'%a)():
                    opt.append('-mcpu='+a)
                    opt.append('-mtune='+a)
                    break
            return opt

        # default march options in case we find nothing better
        if cpu.is_i686():
            march_opt = '-march=i686'
        elif cpu.is_i586():
            march_opt = '-march=i586'
        elif cpu.is_i486():
            march_opt = '-march=i486'
        elif cpu.is_i386():
            march_opt = '-march=i386'
        else:
            march_opt = ''

        gnu_ver =  self.get_version()

        if gnu_ver >= '0.5.26': # gcc 3.0
            if cpu.is_AthlonK6():
                march_opt = '-march=k6'
            elif cpu.is_AthlonK7():
                march_opt = '-march=athlon'

        if gnu_ver >= '3.1.1':
            if cpu.is_AthlonK6_2():
                march_opt = '-march=k6-2'
            elif cpu.is_AthlonK6_3():
                march_opt = '-march=k6-3'
            elif cpu.is_AthlonMP():
                march_opt = '-march=athlon-mp'
                # there's also: athlon-tbird, athlon-4, athlon-xp
            elif cpu.is_Nocona():
                march_opt = '-march=nocona'
            elif cpu.is_Prescott():
                march_opt = '-march=prescott'
            elif cpu.is_PentiumIV():
                march_opt = '-march=pentium4'
            elif cpu.is_PentiumIII():
                march_opt = '-march=pentium3'
            elif cpu.is_PentiumM():
                march_opt = '-march=pentium3'
            elif cpu.is_PentiumII():
                march_opt = '-march=pentium2'

        if gnu_ver >= '3.4':
            if cpu.is_Opteron():
                march_opt = '-march=opteron'
            elif cpu.is_Athlon64():
                march_opt = '-march=athlon64'

        if gnu_ver >= '3.4.4':
            if cpu.is_PentiumM():
                march_opt = '-march=pentium-m'

        # Note: gcc 3.2 on win32 has breakage with -march specified
        if '3.1.1' <= gnu_ver <= '3.4' and sys.platform=='win32':
            march_opt = ''

        if march_opt:
            opt.append(march_opt)

        # other CPU flags
        if gnu_ver >= '3.1.1':
            if cpu.has_mmx(): opt.append('-mmmx')
            if cpu.has_3dnow(): opt.append('-m3dnow')

        if gnu_ver > '3.2.2':
            if cpu.has_sse2(): opt.append('-msse2')
            if cpu.has_sse(): opt.append('-msse')
        if gnu_ver >= '3.4':
            if cpu.has_sse3(): opt.append('-msse3')
        if cpu.is_Intel():
            opt.append('-fomit-frame-pointer')
            if cpu.is_32bit():
                opt.append('-malign-double')
        return opt

class Gnu95FCompiler(GnuFCompiler):

    compiler_type = 'gnu95'
    version_match = simple_version_match(start='GNU Fortran 95')

    # 'gfortran --version' results:
    # Debian: GNU Fortran 95 (GCC 4.0.3 20051023 (prerelease) (Debian 4.0.2-3))
    # OS X: GNU Fortran 95 (GCC) 4.1.0
    #       GNU Fortran 95 (GCC) 4.2.0 20060218 (experimental)

    for fc_exe in map(find_executable,['gfortran','f95']):
        if os.path.isfile(fc_exe):
            break
    executables = {
        'version_cmd'  : [fc_exe,"--version"],
        'compiler_f77' : [fc_exe,"-Wall","-ffixed-form","-fno-second-underscore"],
        'compiler_f90' : [fc_exe,"-Wall","-fno-second-underscore"],
        'compiler_fix' : [fc_exe,"-Wall","-ffixed-form","-fno-second-underscore"],
        'linker_so'    : [fc_exe,"-Wall"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"],
        'linker_exe'   : [fc_exe,"-Wall"]
        }

    # use -mno-cygwin flag for g77 when Python is not Cygwin-Python
    if sys.platform == 'win32':
        for key in ['version_cmd', 'compiler_f77', 'compiler_f90',
                    'compiler_fix', 'linker_so', 'linker_exe']:
            executables[key].append('-mno-cygwin')

    module_dir_switch = '-J'
    module_include_switch = '-I'

    g2c = 'gfortran'

    def get_libraries(self):
        opt = GnuFCompiler.get_libraries(self)
        if sys.platform == 'darwin':
            opt.remove('cc_dynamic')        
        return opt

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    #compiler = new_fcompiler(compiler='gnu')
    compiler = GnuFCompiler()
    compiler.customize()
    print compiler.get_version()


#http://www.compaq.com/fortran/docs/

import os
import sys

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.fcompiler import FCompiler

class CompaqFCompiler(FCompiler):

    compiler_type = 'compaq'
    version_pattern = r'Compaq Fortran (?P<version>[^\s]*).*'

    if sys.platform[:5]=='linux':
        fc_exe = 'fort'
    else:
        fc_exe = 'f90'

    executables = {
        'version_cmd'  : [fc_exe, "-version"],
        'compiler_f77' : [fc_exe, "-f77rtl","-fixed"],
        'compiler_fix' : [fc_exe, "-fixed"],
        'compiler_f90' : [fc_exe],
        'linker_so'    : [fc_exe],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    module_dir_switch = '-module ' # not tested
    module_include_switch = '-I'

    def get_flags(self):
        return ['-assume no2underscore','-nomixed_str_len_arg']
    def get_flags_debug(self):
        return ['-g','-check bounds']
    def get_flags_opt(self):
        return ['-O4','-align dcommons','-assume bigarrays',
                '-assume nozsize','-math_library fast']
    def get_flags_arch(self):
        return ['-arch host', '-tune host']
    def get_flags_linker_so(self):
        if sys.platform[:5]=='linux':
            return ['-shared']
        return ['-shared','-Wl,-expect_unresolved,*']

class CompaqVisualFCompiler(FCompiler):

    compiler_type = 'compaqv'
    version_pattern = r'(DIGITAL|Compaq) Visual Fortran Optimizing Compiler'\
                      ' Version (?P<version>[^\s]*).*'

    compile_switch = '/compile_only'
    object_switch = '/object:'
    library_switch = '/OUT:'      #No space after /OUT:!

    static_lib_extension = ".lib"
    static_lib_format = "%s%s"
    module_dir_switch = '/module:'
    module_include_switch = '/I'

    ar_exe = 'lib.exe'
    fc_exe = 'DF'
    if sys.platform=='win32':
        from distutils.msvccompiler import MSVCCompiler
        m = MSVCCompiler()
        m.initialize()
        ar_exe = m.lib

    executables = {
        'version_cmd'  : ['DF', "/what"],
        'compiler_f77' : ['DF', "/f77rtl","/fixed"],
        'compiler_fix' : ['DF', "/fixed"],
        'compiler_f90' : ['DF'],
        'linker_so'    : ['DF'],
        'archiver'     : [ar_exe, "/OUT:"],
        'ranlib'       : None
        }

    def get_flags(self):
        return ['/nologo','/MD','/WX','/iface=(cref,nomixed_str_len_arg)',
                '/names:lowercase','/assume:underscore']
    def get_flags_opt(self):
        return ['/Ox','/fast','/optimize:5','/unroll:0','/math_library:fast']
    def get_flags_arch(self):
        return ['/threads']
    def get_flags_debug(self):
        return ['/debug']

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='compaq')
    compiler.customize()
    print compiler.get_version()

# http://developer.intel.com/software/products/compilers/flin/

import os
import sys

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.fcompiler import FCompiler, dummy_fortran_file
from numpy.distutils.exec_command import find_executable

class IntelFCompiler(FCompiler):

    compiler_type = 'intel'
    version_pattern = r'Intel\(R\) Fortran Compiler for 32-bit '\
                      'applications, Version (?P<version>[^\s*]*)'

    for fc_exe in map(find_executable,['ifort','ifc']):
        if os.path.isfile(fc_exe):
            break

    executables = {
        'version_cmd'  : [fc_exe, "-FI -V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':dummy_fortran_file()}],
        'compiler_f77' : [fc_exe,"-72","-w90","-w95"],
        'compiler_fix' : [fc_exe,"-FI"],
        'compiler_f90' : [fc_exe],
        'linker_so'    : [fc_exe,"-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    pic_flags = ['-KPIC']
    module_dir_switch = '-module ' # Don't remove ending space!
    module_include_switch = '-I'

    def get_flags(self):
        opt = self.pic_flags + ["-cm"]
        return opt

    def get_flags_free(self):
        return ["-FR"]

    def get_flags_opt(self):
        return ['-O3','-unroll']

    def get_flags_arch(self):
        opt = []
        if cpu.has_fdiv_bug():
            opt.append('-fdiv_check')
        if cpu.has_f00f_bug():
            opt.append('-0f_check')
        if cpu.is_PentiumPro() or cpu.is_PentiumII() or cpu.is_PentiumIII():
            opt.extend(['-tpp6'])
        elif cpu.is_PentiumM():
            opt.extend(['-tpp7','-xB'])
        elif cpu.is_Pentium():
            opt.append('-tpp5')
        elif cpu.is_PentiumIV() or cpu.is_Xeon():
            opt.extend(['-tpp7','-xW'])
        if cpu.has_mmx() and not cpu.is_Xeon():
            opt.append('-xM')
        if cpu.has_sse2():
            opt.append('-arch SSE2')
        elif cpu.has_sse():
            opt.append('-arch SSE')
        return opt

    def get_flags_linker_so(self):
        opt = FCompiler.get_flags_linker_so(self)
        v = self.get_version()
        if v and v >= '8.0':
            opt.append('-nofor_main')
        opt.extend(self.get_flags_arch())
        return opt

class IntelItaniumFCompiler(IntelFCompiler):
    compiler_type = 'intele'
    version_pattern = r'Intel\(R\) Fortran 90 Compiler Itanium\(TM\) Compiler'\
                      ' for the Itanium\(TM\)-based applications,'\
                      ' Version (?P<version>[^\s*]*)'

    for fc_exe in map(find_executable,['ifort','efort','efc']):
        if os.path.isfile(fc_exe):
            break

    executables = {
        'version_cmd'  : [fc_exe, "-FI -V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':dummy_fortran_file()}],
        'compiler_f77' : [fc_exe,"-FI","-w90","-w95"],
        'compiler_fix' : [fc_exe,"-FI"],
        'compiler_f90' : [fc_exe],
        'linker_so'    : [fc_exe,"-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

class IntelEM64TFCompiler(IntelFCompiler):
    compiler_type = 'intelem'

    version_pattern = r'Intel\(R\) Fortran Compiler for Intel\(R\) EM64T-based '\
                      'applications, Version (?P<version>[^\s*]*)'

    for fc_exe in map(find_executable,['ifort','efort','efc']):
        if os.path.isfile(fc_exe):
            break

    executables = {
        'version_cmd'  : [fc_exe, "-FI -V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':dummy_fortran_file()}],
        'compiler_f77' : [fc_exe,"-FI","-w90","-w95"],
        'compiler_fix' : [fc_exe,"-FI"],
        'compiler_f90' : [fc_exe],
        'linker_so'    : [fc_exe,"-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    def get_flags_arch(self):
        opt = []
        if cpu.is_PentiumIV() or cpu.is_Xeon():
            opt.extend(['-tpp7', '-xW'])
        return opt

class IntelVisualFCompiler(FCompiler):

    compiler_type = 'intelv'
    version_pattern = r'Intel\(R\) Fortran Compiler for 32-bit applications, '\
                      'Version (?P<version>[^\s*]*)'

    ar_exe = 'lib.exe'
    fc_exe = 'ifl'
    if sys.platform=='win32':
        from distutils.msvccompiler import MSVCCompiler
        ar_exe = MSVCCompiler().lib

    executables = {
        'version_cmd'  : [fc_exe, "-FI -V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':dummy_fortran_file()}],
        'compiler_f77' : [fc_exe,"-FI","-w90","-w95"],
        'compiler_fix' : [fc_exe,"-FI","-4L72","-w"],
        'compiler_f90' : [fc_exe],
        'linker_so'    : [fc_exe,"-shared"],
        'archiver'     : [ar_exe, "/verbose", "/OUT:"],
        'ranlib'       : None
        }

    compile_switch = '/c '
    object_switch = '/Fo'     #No space after /Fo!
    library_switch = '/OUT:'  #No space after /OUT:!
    module_dir_switch = '/module:' #No space after /module:
    module_include_switch = '/I'

    def get_flags(self):
        opt = ['/nologo','/MD','/nbs','/Qlowercase','/us']
        return opt

    def get_flags_free(self):
        return ["-FR"]

    def get_flags_debug(self):
        return ['/4Yb','/d2']

    def get_flags_opt(self):
        return ['/O3','/Qip','/Qipo','/Qipo_obj']

    def get_flags_arch(self):
        opt = []
        if cpu.is_PentiumPro() or cpu.is_PentiumII():
            opt.extend(['/G6','/Qaxi'])
        elif cpu.is_PentiumIII():
            opt.extend(['/G6','/QaxK'])
        elif cpu.is_Pentium():
            opt.append('/G5')
        elif cpu.is_PentiumIV():
            opt.extend(['/G7','/QaxW'])
        if cpu.has_mmx():
            opt.append('/QaxM')
        return opt

class IntelItaniumVisualFCompiler(IntelVisualFCompiler):

    compiler_type = 'intelev'
    version_pattern = r'Intel\(R\) Fortran 90 Compiler Itanium\(TM\) Compiler'\
                      ' for the Itanium\(TM\)-based applications,'\
                      ' Version (?P<version>[^\s*]*)'

    fc_exe = 'efl' # XXX this is a wild guess
    ar_exe = IntelVisualFCompiler.ar_exe

    executables = {
        'version_cmd'  : [fc_exe, "-FI -V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':dummy_fortran_file()}],
        'compiler_f77' : [fc_exe,"-FI","-w90","-w95"],
        'compiler_fix' : [fc_exe,"-FI","-4L72","-w"],
        'compiler_f90' : [fc_exe],
        'linker_so'    : [fc_exe,"-shared"],
        'archiver'     : [ar_exe, "/verbose", "/OUT:"],
        'ranlib'       : None
        }

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='intel')
    compiler.customize()
    print compiler.get_version()


from numpy.distutils.fcompiler import FCompiler

class NoneFCompiler(FCompiler):

    compiler_type = 'none'

    executables = {'compiler_f77':['/path/to/nowhere/none'],
                   'compiler_f90':['/path/to/nowhere/none'],
                   'compiler_fix':['/path/to/nowhere/none'],
                   'linker_so':['/path/to/nowhere/none'],
                   'archiver':['/path/to/nowhere/none'],
                   'ranlib':['/path/to/nowhere/none'],
                   'version_cmd':['/path/to/nowhere/none'],
                   }


if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    compiler = NoneFCompiler()
    compiler.customize()
    print compiler.get_version()

import os
import sys

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.fcompiler import FCompiler

class NAGFCompiler(FCompiler):

    compiler_type = 'nag'
    version_pattern =  r'NAGWare Fortran 95 compiler Release (?P<version>[^\s]*)'

    executables = {
        'version_cmd'  : ["f95", "-V"],
        'compiler_f77' : ["f95", "-fixed"],
        'compiler_fix' : ["f95", "-fixed"],
        'compiler_f90' : ["f95"],
        'linker_so'    : ["f95"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    def get_flags_linker_so(self):
        if sys.platform=='darwin':
            return ['-unsharedf95','-Wl,-bundle,-flat_namespace,-undefined,suppress']
        return ["-Wl,-shared"]
    def get_flags_opt(self):
        return ['-O4']
    def get_flags_arch(self):
        return ['-target=native']
    def get_flags_debug(self):
        return ['-g','-gline','-g90','-nan','-C']

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='nag')
    compiler.customize()
    print compiler.get_version()


# http://www.pgroup.com

import os
import sys

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.fcompiler import FCompiler

class PGroupFCompiler(FCompiler):

    compiler_type = 'pg'
    version_pattern =  r'\s*pg(f77|f90|hpf) (?P<version>[\d.-]+).*'

    executables = {
        'version_cmd'  : ["pgf77", "-V 2>/dev/null"],
        'compiler_f77' : ["pgf77"],
        'compiler_fix' : ["pgf90", "-Mfixed"],
        'compiler_f90' : ["pgf90"],
        'linker_so'    : ["pgf90","-shared","-fpic"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }
    pic_flags = ['-fpic']
    module_dir_switch = '-module '
    module_include_switch = '-I'

    def get_flags(self):
        opt = ['-Minform=inform','-Mnosecond_underscore']
        return self.pic_flags + opt
    def get_flags_opt(self):
        return ['-fast']
    def get_flags_debug(self):
        return ['-g']

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='pg')
    compiler.customize()
    print compiler.get_version()

import os
import re
import sys

from numpy.distutils.fcompiler import FCompiler
from distutils import log

class IbmFCompiler(FCompiler):

    compiler_type = 'ibm'
    version_pattern =  r'xlf\(1\)\s*IBM XL Fortran (Advanced Edition |)Version (?P<version>[^\s*]*)'

    executables = {
        'version_cmd'  : ["xlf"],
        'compiler_f77' : ["xlf"],
        'compiler_fix' : ["xlf90", "-qfixed"],
        'compiler_f90' : ["xlf90"],
        'linker_so'    : ["xlf95"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    def get_version(self,*args,**kwds):
        version = FCompiler.get_version(self,*args,**kwds)
        xlf_dir = '/etc/opt/ibmcmp/xlf'
        if version is None and os.path.isdir(xlf_dir):
            # If the output of xlf does not contain version info
            # (that's the case with xlf 8.1, for instance) then
            # let's try another method:
            l = os.listdir(xlf_dir)
            l.sort()
            l.reverse()
            l = [d for d in l if os.path.isfile(os.path.join(xlf_dir,d,'xlf.cfg'))]
            if l:
                from distutils.version import LooseVersion
                self.version = version = LooseVersion(l[0])
        return version

    def get_flags(self):
        return ['-qextname']

    def get_flags_debug(self):
        return ['-g']

    def get_flags_linker_so(self):
        opt = []
        if sys.platform=='darwin':
            opt.append('-Wl,-bundle,-flat_namespace,-undefined,suppress')
        else:
            opt.append('-bshared')
        version = self.get_version(ok_status=[0,40])
        if version is not None:
            import tempfile
            xlf_cfg = '/etc/opt/ibmcmp/xlf/%s/xlf.cfg' % version
            new_cfg = tempfile.mktemp()+'_xlf.cfg'
            log.info('Creating '+new_cfg)
            fi = open(xlf_cfg,'r')
            fo = open(new_cfg,'w')
            crt1_match = re.compile(r'\s*crt\s*[=]\s*(?P<path>.*)/crt1.o').match
            for line in fi.readlines():
                m = crt1_match(line)
                if m:
                    fo.write('crt = %s/bundle1.o\n' % (m.group('path')))
                else:
                    fo.write(line)
            fi.close()
            fo.close()
            opt.append('-F'+new_cfg)
        return opt

    def get_flags_opt(self):
        return ['-O5']

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    #compiler = new_fcompiler(compiler='ibm')
    compiler = IbmFCompiler()
    compiler.customize()
    print compiler.get_version()

import os
import sys

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.ccompiler import simple_version_match
from numpy.distutils.fcompiler import FCompiler

class SunFCompiler(FCompiler):

    compiler_type = 'sun'
    # ex:
    # f90: Sun WorkShop 6 update 2 Fortran 95 6.2 Patch 111690-10 2003/08/28
    version_match = simple_version_match(
                      start=r'f9[05]: (Sun|Forte|WorkShop).*Fortran 95')

    executables = {
        'version_cmd'  : ["f90", "-V"],
        'compiler_f77' : ["f90"],
        'compiler_fix' : ["f90", "-fixed"],
        'compiler_f90' : ["f90"],
        'linker_so'    : ["f90","-Bdynamic","-G"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }
    module_dir_switch = '-moddir='
    module_include_switch = '-M'
    pic_flags = ['-xcode=pic32']

    def get_flags_f77(self):
        ret = ["-ftrap=%none"]
        if (self.get_version() or '') >= '7':
            ret.append("-f77")
        else:
            ret.append("-fixed")
        return ret
    def get_opt(self):
        return ['-fast','-dalign']
    def get_arch(self):
        return ['-xtarget=generic']
    def get_libraries(self):
        opt = []
        opt.extend(['fsu','sunmath','mvec','f77compat'])
        return opt

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='sun')
    compiler.customize()
    print compiler.get_version()

import os
import sys

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.fcompiler import FCompiler

class LaheyFCompiler(FCompiler):

    compiler_type = 'lahey'
    version_pattern =  r'Lahey/Fujitsu Fortran 95 Compiler Release (?P<version>[^\s*]*)'

    executables = {
        'version_cmd'  : ["lf95", "--version"],
        'compiler_f77' : ["lf95", "--fix"],
        'compiler_fix' : ["lf95", "--fix"],
        'compiler_f90' : ["lf95"],
        'linker_so'    : ["lf95","-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    module_dir_switch = None  #XXX Fix me
    module_include_switch = None #XXX Fix me

    def get_flags_opt(self):
        return ['-O']
    def get_flags_debug(self):
        return ['-g','--chk','--chkglobal']
    def get_library_dirs(self):
        opt = []
        d = os.environ.get('LAHEY')
        if d:
            opt.append(os.path.join(d,'lib'))
        return opt
    def get_libraries(self):
        opt = []
        opt.extend(['fj9f6', 'fj9i6', 'fj9ipp', 'fj9e6'])
        return opt

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='lahey')
    compiler.customize()
    print compiler.get_version()

"""numpy.distutils.fcompiler

Contains FCompiler, an abstract base class that defines the interface
for the numpy.distutils Fortran compiler abstraction model.
"""

__all__ = ['FCompiler','new_fcompiler','show_fcompilers',
           'dummy_fortran_file']

import os
import sys
import re
from types import StringType,NoneType
from distutils.sysconfig import get_config_var
from distutils.fancy_getopt import FancyGetopt
from distutils.errors import DistutilsModuleError,DistutilsArgError,\
     DistutilsExecError,CompileError,LinkError,DistutilsPlatformError
from distutils.util import split_quoted

from numpy.distutils.ccompiler import CCompiler, gen_lib_options
from numpy.distutils import log
from numpy.distutils.command.config_compiler import config_fc
from numpy.distutils.core import get_distribution
from numpy.distutils.misc_util import is_string, is_sequence
from distutils.spawn import _nt_quote_args

class FCompiler(CCompiler):
    """ Abstract base class to define the interface that must be implemented
    by real Fortran compiler classes.

    Methods that subclasses may redefine:

        get_version_cmd(), get_linker_so(), get_version()
        get_flags(), get_flags_opt(), get_flags_arch(), get_flags_debug()
        get_flags_f77(), get_flags_opt_f77(), get_flags_arch_f77(),
        get_flags_debug_f77(), get_flags_f90(), get_flags_opt_f90(),
        get_flags_arch_f90(), get_flags_debug_f90(),
        get_flags_fix(), get_flags_linker_so(), get_flags_version()

    DON'T call these methods (except get_version) after
    constructing a compiler instance or inside any other method.
    All methods, except get_version_cmd() and get_flags_version(), may
    call get_version() method.

    After constructing a compiler instance, always call customize(dist=None)
    method that finalizes compiler construction and makes the following
    attributes available:
      compiler_f77
      compiler_f90
      compiler_fix
      linker_so
      archiver
      ranlib
      libraries
      library_dirs
    """


    language_map = {'.f':'f77',
                    '.for':'f77',
                    '.F':'f77',    # XXX: needs preprocessor
                    '.ftn':'f77',
                    '.f77':'f77',
                    '.f90':'f90',
                    '.F90':'f90',  # XXX: needs preprocessor
                    '.f95':'f90',
                    }
    language_order = ['f90','f77']

    version_pattern = None

    executables = {
        'version_cmd'  : ["f77","-v"],
        'compiler_f77' : ["f77"],
        'compiler_f90' : ["f90"],
        'compiler_fix' : ["f90","-fixed"],
        'linker_so'    : ["f90","-shared"],
        'linker_exe'   : ["f90"],
        'archiver'     : ["ar","-cr"],
        'ranlib'       : None,
        }

    compile_switch = "-c"
    object_switch = "-o "   # Ending space matters! It will be stripped
                            # but if it is missing then object_switch
                            # will be prefixed to object file name by
                            # string concatenation.
    library_switch = "-o "  # Ditto!

    # Switch to specify where module files are created and searched
    # for USE statement.  Normally it is a string and also here ending
    # space matters. See above.
    module_dir_switch = None

    # Switch to specify where module files are searched for USE statement.
    module_include_switch = '-I'

    pic_flags = []           # Flags to create position-independent code

    src_extensions = ['.for','.ftn','.f77','.f','.f90','.f95','.F','.F90']
    obj_extension = ".o"
    shared_lib_extension = get_config_var('SO')  # or .dll
    static_lib_extension = ".a"  # or .lib
    static_lib_format = "lib%s%s" # or %s%s
    shared_lib_format = "%s%s"
    exe_extension = ""

    ######################################################################
    ## Methods that subclasses may redefine. But don't call these methods!
    ## They are private to FCompiler class and may return unexpected
    ## results if used elsewhere. So, you have been warned..

    def get_version_cmd(self):
        """ Compiler command to print out version information. """
        f77 = self.executables['compiler_f77']
        if f77 is not None:
            f77 = f77[0]
        cmd = self.executables['version_cmd']
        if cmd is not None:
            cmd = cmd[0]
            if cmd==f77:
                cmd = self.compiler_f77[0]
            else:
                f90 = self.executables['compiler_f90']
                if f90 is not None:
                    f90 = f90[0]
                if cmd==f90:
                    cmd = self.compiler_f90[0]
        return cmd

    def get_linker_so(self):
        """ Linker command to build shared libraries. """
        f77 = self.executables['compiler_f77']
        if f77 is not None:
            f77 = f77[0]
        ln = self.executables['linker_so']
        if ln is not None:
            ln = ln[0]
            if ln==f77:
                ln = self.compiler_f77[0]
            else:
                f90 = self.executables['compiler_f90']
                if f90 is not None:
                    f90 = f90[0]
                if ln==f90:
                    ln = self.compiler_f90[0]
        return ln

    def get_linker_exe(self):
        """ Linker command to build shared libraries. """
        f77 = self.executables['compiler_f77']
        if f77 is not None:
            f77 = f77[0]
        ln = self.executables.get('linker_exe')
        if ln is not None:
            ln = ln[0]
            if ln==f77:
                ln = self.compiler_f77[0]
            else:
                f90 = self.executables['compiler_f90']
                if f90 is not None:
                    f90 = f90[0]
                if ln==f90:
                    ln = self.compiler_f90[0]
        return ln

    def get_flags(self):
        """ List of flags common to all compiler types. """
        return [] + self.pic_flags
    def get_flags_version(self):
        """ List of compiler flags to print out version information. """
        if self.executables['version_cmd']:
            return self.executables['version_cmd'][1:]
        return []
    def get_flags_f77(self):
        """ List of Fortran 77 specific flags. """
        if self.executables['compiler_f77']:
            return self.executables['compiler_f77'][1:]
        return []
    def get_flags_f90(self):
        """ List of Fortran 90 specific flags. """
        if self.executables['compiler_f90']:
            return self.executables['compiler_f90'][1:]
        return []
    def get_flags_free(self):
        """ List of Fortran 90 free format specific flags. """
        return []
    def get_flags_fix(self):
        """ List of Fortran 90 fixed format specific flags. """
        if self.executables['compiler_fix']:
            return self.executables['compiler_fix'][1:]
        return []
    def get_flags_linker_so(self):
        """ List of linker flags to build a shared library. """
        if self.executables['linker_so']:
            return self.executables['linker_so'][1:]
        return []
    def get_flags_linker_exe(self):
        """ List of linker flags to build an executable. """
        if self.executables['linker_exe']:
            return self.executables['linker_exe'][1:]
        return []
    def get_flags_ar(self):
        """ List of archiver flags. """
        if self.executables['archiver']:
            return self.executables['archiver'][1:]
        return []
    def get_flags_opt(self):
        """ List of architecture independent compiler flags. """
        return []
    def get_flags_arch(self):
        """ List of architecture dependent compiler flags. """
        return []
    def get_flags_debug(self):
        """ List of compiler flags to compile with debugging information. """
        return []

    get_flags_opt_f77 = get_flags_opt_f90 = get_flags_opt
    get_flags_arch_f77 = get_flags_arch_f90 = get_flags_arch
    get_flags_debug_f77 = get_flags_debug_f90 = get_flags_debug

    def get_libraries(self):
        """ List of compiler libraries. """
        return self.libraries[:]
    def get_library_dirs(self):
        """ List of compiler library directories. """
        return self.library_dirs[:]

    ############################################################

    ## Public methods:

    def customize(self, dist):
        """ Customize Fortran compiler.

        This method gets Fortran compiler specific information from
        (i) class definition, (ii) environment, (iii) distutils config
        files, and (iv) command line.

        This method should be always called after constructing a
        compiler instance. But not in __init__ because Distribution
        instance is needed for (iii) and (iv).
        """
        log.info('customize %s' % (self.__class__.__name__))
        from distutils.dist import Distribution
        if dist is None:
            # These hooks are for testing only!
            dist = Distribution()
#            dist.script_name = os.path.basename(sys.argv[0])
#            dist.script_args = ['config_fc'] + sys.argv[1:]
#            dist.cmdclass['config_fc'] = config_fc
#            dist.parse_config_files()
#            dist.parse_command_line()
        if isinstance(dist, Distribution):
            conf = dist.get_option_dict('config_fc')
        else:
            assert isinstance(dist,dict)
            conf = dist
        noopt = conf.get('noopt',[None,0])[1]
        if 0: # change to `if 1:` when making release.
            # Don't use architecture dependent compiler flags:
            noarch = 1
        else:
            noarch = conf.get('noarch',[None,noopt])[1]
        debug = conf.get('debug',[None,0])[1]

        f77 = self.__get_cmd('compiler_f77','F77',(conf,'f77exec'))
        f90 = self.__get_cmd('compiler_f90','F90',(conf,'f90exec'))
        # Temporarily setting f77,f90 compilers so that
        # version_cmd can use their executables.
        if f77:
            self.set_executables(compiler_f77=[f77])
        if f90:
            self.set_executables(compiler_f90=[f90])

        # Must set version_cmd before others as self.get_flags*
        # methods may call self.get_version.
        vers_cmd = self.__get_cmd(self.get_version_cmd)
        if vers_cmd:
            vflags = self.__get_flags(self.get_flags_version)
            self.set_executables(version_cmd=[vers_cmd]+vflags)

        if f77:
            f77flags = self.__get_flags(self.get_flags_f77,'F77FLAGS',
                                   (conf,'f77flags'))
        if f90:
            f90flags = self.__get_flags(self.get_flags_f90,'F90FLAGS',
                                       (conf,'f90flags'))
            freeflags = self.__get_flags(self.get_flags_free,'FREEFLAGS',
                                         (conf,'freeflags'))
        # XXX Assuming that free format is default for f90 compiler.
        fix = self.__get_cmd('compiler_fix','F90',(conf,'f90exec'))
        if fix:
            fixflags = self.__get_flags(self.get_flags_fix) + f90flags

        oflags,aflags,dflags = [],[],[]
        if not noopt:
            oflags = self.__get_flags(self.get_flags_opt,'FOPT',(conf,'opt'))
            if f77 and self.get_flags_opt is not self.get_flags_opt_f77:
                f77flags += self.__get_flags(self.get_flags_opt_f77)
            if f90 and self.get_flags_opt is not self.get_flags_opt_f90:
                f90flags += self.__get_flags(self.get_flags_opt_f90)
            if fix and self.get_flags_opt is not self.get_flags_opt_f90:
                fixflags += self.__get_flags(self.get_flags_opt_f90)
            if not noarch:
                aflags = self.__get_flags(self.get_flags_arch,'FARCH',
                                          (conf,'arch'))
                if f77 and self.get_flags_arch is not self.get_flags_arch_f77:
                    f77flags += self.__get_flags(self.get_flags_arch_f77)
                if f90 and self.get_flags_arch is not self.get_flags_arch_f90:
                    f90flags += self.__get_flags(self.get_flags_arch_f90)
                if fix and self.get_flags_arch is not self.get_flags_arch_f90:
                    fixflags += self.__get_flags(self.get_flags_arch_f90)
        if debug:
            dflags = self.__get_flags(self.get_flags_debug,'FDEBUG')
            if f77  and self.get_flags_debug is not self.get_flags_debug_f77:
                f77flags += self.__get_flags(self.get_flags_debug_f77)
            if f90  and self.get_flags_debug is not self.get_flags_debug_f90:
                f90flags += self.__get_flags(self.get_flags_debug_f90)
            if fix and self.get_flags_debug is not self.get_flags_debug_f90:
                fixflags += self.__get_flags(self.get_flags_debug_f90)

        fflags = self.__get_flags(self.get_flags,'FFLAGS') \
                 + dflags + oflags + aflags

        if f77:
            self.set_executables(compiler_f77=[f77]+f77flags+fflags)
        if f90:
            self.set_executables(compiler_f90=[f90]+freeflags+f90flags+fflags)
        if fix:
            self.set_executables(compiler_fix=[fix]+fixflags+fflags)
        #XXX: Do we need LDSHARED->SOSHARED, LDFLAGS->SOFLAGS
        linker_so = self.__get_cmd(self.get_linker_so,'LDSHARED')
        if linker_so:
            linker_so_flags = self.__get_flags(self.get_flags_linker_so,'LDFLAGS')
            self.set_executables(linker_so=[linker_so]+linker_so_flags)

        linker_exe = self.__get_cmd(self.get_linker_exe,'LD')
        if linker_exe:
            linker_exe_flags = self.__get_flags(self.get_flags_linker_exe,'LDFLAGS')
            self.set_executables(linker_exe=[linker_exe]+linker_exe_flags)
        ar = self.__get_cmd('archiver','AR')
        if ar:
            arflags = self.__get_flags(self.get_flags_ar,'ARFLAGS')
            self.set_executables(archiver=[ar]+arflags)

        ranlib = self.__get_cmd('ranlib','RANLIB')
        if ranlib:
            self.set_executables(ranlib=[ranlib])

        self.set_library_dirs(self.get_library_dirs())
        self.set_libraries(self.get_libraries())


        verbose = conf.get('verbose',[None,0])[1]
        if verbose:
            self.dump_properties()
        return

    def dump_properties(self):
        """ Print out the attributes of a compiler instance. """
        props = []
        for key in self.executables.keys() + \
                ['version','libraries','library_dirs',
                 'object_switch','compile_switch']:
            if hasattr(self,key):
                v = getattr(self,key)
                props.append((key, None, '= '+`v`))
        props.sort()

        pretty_printer = FancyGetopt(props)
        for l in pretty_printer.generate_help("%s instance properties:" \
                                              % (self.__class__.__name__)):
            if l[:4]=='  --':
                l = '  ' + l[4:]
            print l
        return

    ###################

    def _compile(self, obj, src, ext, cc_args, extra_postargs, pp_opts):
        """Compile 'src' to product 'obj'."""
        src_flags = {}
        if is_f_file(src) and not has_f90_header(src):
            flavor = ':f77'
            compiler = self.compiler_f77
            src_flags = get_f77flags(src)
        elif is_free_format(src):
            flavor = ':f90'
            compiler = self.compiler_f90
            if compiler is None:
                raise DistutilsExecError, 'f90 not supported by '\
                      +self.__class__.__name__
        else:
            flavor = ':fix'
            compiler = self.compiler_fix
            if compiler is None:
                raise DistutilsExecError, 'f90 (fixed) not supported by '\
                      +self.__class__.__name__
        if self.object_switch[-1]==' ':
            o_args = [self.object_switch.strip(),obj]
        else:
            o_args = [self.object_switch.strip()+obj]

        assert self.compile_switch.strip()
        s_args = [self.compile_switch, src]

        extra_flags = src_flags.get(self.compiler_type,[])
        if extra_flags:
            log.info('using compile options from source: %r' \
                     % ' '.join(extra_flags))

        if os.name == 'nt':
            compiler = _nt_quote_args(compiler)
        command = compiler + cc_args + extra_flags + s_args + o_args + extra_postargs

        display = '%s: %s' % (os.path.basename(compiler[0]) + flavor,
                              src)
        try:
            self.spawn(command,display=display)
        except DistutilsExecError, msg:
            raise CompileError, msg

        return

    def module_options(self, module_dirs, module_build_dir):
        options = []
        if self.module_dir_switch is not None:
            if self.module_dir_switch[-1]==' ':
                options.extend([self.module_dir_switch.strip(),module_build_dir])
            else:
                options.append(self.module_dir_switch.strip()+module_build_dir)
        else:
            print 'XXX: module_build_dir=%r option ignored' % (module_build_dir)
            print 'XXX: Fix module_dir_switch for ',self.__class__.__name__
        if self.module_include_switch is not None:
            for d in [module_build_dir]+module_dirs:
                options.append('%s%s' % (self.module_include_switch, d))
        else:
            print 'XXX: module_dirs=%r option ignored' % (module_dirs)
            print 'XXX: Fix module_include_switch for ',self.__class__.__name__
        return options

    def library_option(self, lib):
        return "-l" + lib
    def library_dir_option(self, dir):
        return "-L" + dir

    def link(self, target_desc, objects,
             output_filename, output_dir=None, libraries=None,
             library_dirs=None, runtime_library_dirs=None,
             export_symbols=None, debug=0, extra_preargs=None,
             extra_postargs=None, build_temp=None, target_lang=None):
        objects, output_dir = self._fix_object_args(objects, output_dir)
        libraries, library_dirs, runtime_library_dirs = \
            self._fix_lib_args(libraries, library_dirs, runtime_library_dirs)

        lib_opts = gen_lib_options(self, library_dirs, runtime_library_dirs,
                                   libraries)
        if is_string(output_dir):
            output_filename = os.path.join(output_dir, output_filename)
        elif output_dir is not None:
            raise TypeError, "'output_dir' must be a string or None"

        if self._need_link(objects, output_filename):
            if self.library_switch[-1]==' ':
                o_args = [self.library_switch.strip(),output_filename]
            else:
                o_args = [self.library_switch.strip()+output_filename]

            if is_string(self.objects):
                ld_args = objects + [self.objects]
            else:
                ld_args = objects + self.objects
            ld_args = ld_args + lib_opts + o_args
            if debug:
                ld_args[:0] = ['-g']
            if extra_preargs:
                ld_args[:0] = extra_preargs
            if extra_postargs:
                ld_args.extend(extra_postargs)
            self.mkpath(os.path.dirname(output_filename))
            if target_desc == CCompiler.EXECUTABLE:
                linker = self.linker_exe[:]
            else:
                linker = self.linker_so[:]
            if os.name == 'nt':
                linker = _nt_quote_args(linker)
            command = linker + ld_args
            try:
                self.spawn(command)
            except DistutilsExecError, msg:
                raise LinkError, msg
        else:
            log.debug("skipping %s (up-to-date)", output_filename)
        return


    ## Private methods:

    def __get_cmd(self, command, envvar=None, confvar=None):
        if command is None:
            var = None
        elif is_string(command):
            var = self.executables[command]
            if var is not None:
                var = var[0]
        else:
            var = command()
        if envvar is not None:
            var = os.environ.get(envvar, var)
        if confvar is not None:
            var = confvar[0].get(confvar[1], [None,var])[1]
        return var

    def __get_flags(self, command, envvar=None, confvar=None):
        if command is None:
            var = []
        elif is_string(command):
            var = self.executables[command][1:]
        else:
            var = command()
        if envvar is not None:
            var = os.environ.get(envvar, var)
        if confvar is not None:
            var = confvar[0].get(confvar[1], [None,var])[1]
        if is_string(var):
            var = split_quoted(var)
        return var

    ## class FCompiler

fcompiler_class = {'gnu':('gnu','GnuFCompiler',
                          "GNU Fortran Compiler"),
                   'gnu95':('gnu','Gnu95FCompiler',
                            "GNU 95 Fortran Compiler"),
                   'g95':('g95','G95FCompiler',
                          "G95 Fortran Compiler"),
                   'pg':('pg','PGroupFCompiler',
                         "Portland Group Fortran Compiler"),
                   'absoft':('absoft','AbsoftFCompiler',
                             "Absoft Corp Fortran Compiler"),
                   'mips':('mips','MipsFCompiler',
                           "MIPSpro Fortran Compiler"),
                   'sun':('sun','SunFCompiler',
                          "Sun|Forte Fortran 95 Compiler"),
                   'intel':('intel','IntelFCompiler',
                            "Intel Fortran Compiler for 32-bit apps"),
                   'intelv':('intel','IntelVisualFCompiler',
                             "Intel Visual Fortran Compiler for 32-bit apps"),
                   'intele':('intel','IntelItaniumFCompiler',
                             "Intel Fortran Compiler for Itanium apps"),
                   'intelev':('intel','IntelItaniumVisualFCompiler',
                              "Intel Visual Fortran Compiler for Itanium apps"),
                   'intelem':('intel','IntelEM64TFCompiler',
                             "Intel Fortran Compiler for EM64T-based apps"),
                   'nag':('nag','NAGFCompiler',
                          "NAGWare Fortran 95 Compiler"),
                   'compaq':('compaq','CompaqFCompiler',
                             "Compaq Fortran Compiler"),
                   'compaqv':('compaq','CompaqVisualFCompiler',
                             "DIGITAL|Compaq Visual Fortran Compiler"),
                   'vast':('vast','VastFCompiler',
                           "Pacific-Sierra Research Fortran 90 Compiler"),
                   'hpux':('hpux','HPUXFCompiler',
                           "HP Fortran 90 Compiler"),
                   'lahey':('lahey','LaheyFCompiler',
                            "Lahey/Fujitsu Fortran 95 Compiler"),
                   'ibm':('ibm','IbmFCompiler',
                          "IBM XL Fortran Compiler"),
                   'f':('f','FFCompiler',
                        "Fortran Company/NAG F Compiler"),
                   'none':('none','NoneFCompiler',"Fake Fortran compiler")
                   }

_default_compilers = (
    # Platform mappings
    ('win32',('gnu','intelv','absoft','compaqv','intelev','gnu95','g95')),
    ('cygwin.*',('gnu','intelv','absoft','compaqv','intelev','gnu95','g95')),
    ('linux.*',('gnu','intel','lahey','pg','absoft','nag','vast','compaq',
                'intele','intelem','gnu95','g95')),
    ('darwin.*',('nag','absoft','ibm','gnu','gnu95','g95')),
    ('sunos.*',('sun','gnu','gnu95','g95')),
    ('irix.*',('mips','gnu','gnu95',)),
    ('aix.*',('ibm','gnu','gnu95',)),
    # OS mappings
    ('posix',('gnu','gnu95',)),
    ('nt',('gnu','gnu95',)),
    ('mac',('gnu','gnu95',)),
    )

def _find_existing_fcompiler(compilers, osname=None, platform=None):
    dist = get_distribution(always=True)
    for compiler in compilers:
        v = None
        try:
            c = new_fcompiler(plat=platform, compiler=compiler)
            c.customize(dist)
            v = c.get_version()
        except DistutilsModuleError:
            pass
        except Exception, e:
            log.warn(str(e))
        if v is not None:
            return compiler
    return

def get_default_fcompiler(osname=None, platform=None):
    """ Determine the default Fortran compiler to use for the given platform. """
    if osname is None:
        osname = os.name
    if platform is None:
        platform = sys.platform
    matching_compilers = []
    for pattern, compiler in _default_compilers:
        if re.match(pattern, platform) is not None or \
               re.match(pattern, osname) is not None:
            if is_sequence(compiler):
                matching_compilers.extend(list(compiler))
            else:
                matching_compilers.append(compiler)
    if not matching_compilers:
        matching_compilers.append('gnu')
    compiler =  _find_existing_fcompiler(matching_compilers,
                                         osname=osname,
                                         platform=platform)
    if compiler is not None:
        return compiler
    return matching_compilers[0]

def new_fcompiler(plat=None,
                  compiler=None,
                  verbose=0,
                  dry_run=0,
                  force=0):
    """ Generate an instance of some FCompiler subclass for the supplied
    platform/compiler combination.
    """
    if plat is None:
        plat = os.name
    try:
        if compiler is None:
            compiler = get_default_fcompiler(plat)
        (module_name, class_name, long_description) = fcompiler_class[compiler]
    except KeyError:
        msg = "don't know how to compile Fortran code on platform '%s'" % plat
        if compiler is not None:
            msg = msg + " with '%s' compiler." % compiler
            msg = msg + " Supported compilers are: %s)" \
                  % (','.join(fcompiler_class.keys()))
        raise DistutilsPlatformError, msg

    try:
        module_name = 'numpy.distutils.fcompiler.'+module_name
        __import__ (module_name)
        module = sys.modules[module_name]
        klass = vars(module)[class_name]
    except ImportError:
        raise DistutilsModuleError, \
              "can't compile Fortran code: unable to load module '%s'" % \
              module_name
    except KeyError:
        raise DistutilsModuleError, \
              ("can't compile Fortran code: unable to find class '%s' " +
               "in module '%s'") % (class_name, module_name)
    compiler = klass(None, dry_run, force)
    log.debug('new_fcompiler returns %s' % (klass))
    return compiler

def show_fcompilers(dist = None):
    """ Print list of available compilers (used by the "--help-fcompiler"
    option to "config_fc").
    """
    if dist is None:
        from distutils.dist import Distribution
        dist = Distribution()
        dist.script_name = os.path.basename(sys.argv[0])
        dist.script_args = ['config_fc'] + sys.argv[1:]
        dist.cmdclass['config_fc'] = config_fc
        dist.parse_config_files()
        dist.parse_command_line()

    compilers = []
    compilers_na = []
    compilers_ni = []
    for compiler in fcompiler_class.keys():
        v = 'N/A'
        try:
            c = new_fcompiler(compiler=compiler)
            c.customize(dist)
            v = c.get_version()
        except DistutilsModuleError:
            pass
        except Exception, msg:
            log.warn(msg)
        if v is None:
            compilers_na.append(("fcompiler="+compiler, None,
                              fcompiler_class[compiler][2]))
        elif v=='N/A':
            compilers_ni.append(("fcompiler="+compiler, None,
                                 fcompiler_class[compiler][2]))
        else:
            compilers.append(("fcompiler="+compiler, None,
                              fcompiler_class[compiler][2] + ' (%s)' % v))

    compilers.sort()
    compilers_na.sort()
    pretty_printer = FancyGetopt(compilers)
    pretty_printer.print_help("List of available Fortran compilers:")
    pretty_printer = FancyGetopt(compilers_na)
    pretty_printer.print_help("List of unavailable Fortran compilers:")
    if compilers_ni:
        pretty_printer = FancyGetopt(compilers_ni)
        pretty_printer.print_help("List of unimplemented Fortran compilers:")
    print "For compiler details, run 'config_fc --verbose' setup command."

def dummy_fortran_file():
    import atexit
    import tempfile
    dummy_name = tempfile.mktemp()+'__dummy'
    dummy = open(dummy_name+'.f','w')
    dummy.write("      subroutine dummy()\n      end\n")
    dummy.close()
    def rm_file(name=dummy_name,log_threshold=log._global_log.threshold):
        save_th = log._global_log.threshold
        log.set_threshold(log_threshold)
        try: os.remove(name+'.f'); log.debug('removed '+name+'.f')
        except OSError: pass
        try: os.remove(name+'.o'); log.debug('removed '+name+'.o')
        except OSError: pass
        log.set_threshold(save_th)
    atexit.register(rm_file)
    return dummy_name

is_f_file = re.compile(r'.*[.](for|ftn|f77|f)\Z',re.I).match
_has_f_header = re.compile(r'-[*]-\s*fortran\s*-[*]-',re.I).search
_has_f90_header = re.compile(r'-[*]-\s*f90\s*-[*]-',re.I).search
_has_fix_header = re.compile(r'-[*]-\s*fix\s*-[*]-',re.I).search
_free_f90_start = re.compile(r'[^c*]\s*[^\s\d\t]',re.I).match
def is_free_format(file):
    """Check if file is in free format Fortran."""
    # f90 allows both fixed and free format, assuming fixed unless
    # signs of free format are detected.
    result = 0
    f = open(file,'r')
    line = f.readline()
    n = 15 # the number of non-comment lines to scan for hints
    if _has_f_header(line):
        n = 0
    elif _has_f90_header(line):
        n = 0
        result = 1
    while n>0 and line:
        if line[0]!='!':
            n -= 1
            if (line[0]!='\t' and _free_f90_start(line[:5])) or line[-2:-1]=='&':
                result = 1
                break
        line = f.readline()
    f.close()
    return result

def has_f90_header(src):
    f = open(src,'r')
    line = f.readline()
    f.close()
    return _has_f90_header(line) or _has_fix_header(line)

_f77flags_re = re.compile(r'(c|)f77flags\s*\(\s*(?P<fcname>\w+)\s*\)\s*=\s*(?P<fflags>.*)',re.I)
def get_f77flags(src):
    """
    Search the first 20 lines of fortran 77 code for line pattern
      `CF77FLAGS(<fcompiler type>)=<f77 flags>`
    Return a dictionary {<fcompiler type>:<f77 flags>}.
    """
    flags = {}
    f = open(src,'r')
    i = 0
    for line in f.readlines():
        i += 1
        if i>20: break
        m = _f77flags_re.match(line)
        if not m: continue
        fcname = m.group('fcname').strip()
        fflags = m.group('fflags').strip()
        flags[fcname] = split_quoted(fflags)
    f.close()
    return flags

if __name__ == '__main__':
    show_fcompilers()

# http://g95.sourceforge.net/

import os
import sys

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.fcompiler import FCompiler

class G95FCompiler(FCompiler):

    compiler_type = 'g95'
    version_pattern = r'G95 \((GCC (?P<gccversion>[\d.]+)|.*?) \(g95!\) (?P<version>.*)\).*'

    # $ g95 --version
    # G95 (GCC 4.0.3 (g95!) May 22 2006)

    executables = {
        'version_cmd'  : ["g95", "--version"],
        'compiler_f77' : ["g95", "-ffixed-form"],
        'compiler_fix' : ["g95", "-ffixed-form"],
        'compiler_f90' : ["g95"],
        'linker_so'    : ["g95","-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }
    pic_flags = ['-fpic']
    module_dir_switch = '-fmod='
    module_include_switch = '-I'

    def get_flags(self):
        return ['-fno-second-underscore']
    def get_flags_opt(self):
        return ['-O']
    def get_flags_debug(self):
        return ['-g']

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    #compiler = new_fcompiler(compiler='g95')
    compiler = G95FCompiler()
    compiler.customize()
    print compiler.get_version()

import os
import sys

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.fcompiler import FCompiler

class MipsFCompiler(FCompiler):

    compiler_type = 'mips'
    version_pattern =  r'MIPSpro Compilers: Version (?P<version>[^\s*,]*)'

    executables = {
        'version_cmd'  : ["f90", "-version"],
        'compiler_f77' : ["f77", "-f77"],
        'compiler_fix' : ["f90", "-fixedform"],
        'compiler_f90' : ["f90"],
        'linker_so'    : ["f90","-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : None
        }
    module_dir_switch = None #XXX: fix me
    module_include_switch = None #XXX: fix me
    pic_flags = ['-KPIC']

    def get_flags(self):
        return self.pic_flags + ['-n32']
    def get_flags_opt(self):
        return ['-O3']
    def get_flags_arch(self):
        opt = []
        for a in '19 20 21 22_4k 22_5k 24 25 26 27 28 30 32_5k 32_10k'.split():
            if getattr(cpu,'is_IP%s'%a)():
                opt.append('-TARG:platform=IP%s' % a)
                break
        return opt
    def get_flags_arch_f77(self):
        r = None
        if cpu.is_r10000(): r = 10000
        elif cpu.is_r12000(): r = 12000
        elif cpu.is_r8000(): r = 8000
        elif cpu.is_r5000(): r = 5000
        elif cpu.is_r4000(): r = 4000
        if r is not None:
            return ['r%s' % (r)]
        return []
    def get_flags_arch_f90(self):
        r = self.get_flags_arch_f77()
        if r:
            r[0] = '-' + r[0]
        return r

if __name__ == '__main__':
    from numpy.distutils.fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='mips')
    compiler.customize()
    print compiler.get_version()

import os
import sys

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.fcompiler import FCompiler

class HPUXFCompiler(FCompiler):

    compiler_type = 'hpux'
    version_pattern =  r'HP F90 (?P<version>[^\s*,]*)'

    executables = {
        'version_cmd'  : ["f90", "+version"],
        'compiler_f77' : ["f90"],
        'compiler_fix' : ["f90"],
        'compiler_f90' : ["f90"],
        'linker_so'    : None,
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }
    module_dir_switch = None #XXX: fix me
    module_include_switch = None #XXX: fix me
    pic_flags = ['+pic=long']
    def get_flags(self):
        return self.pic_flags + ['+ppu']
    def get_flags_opt(self):
        return ['-O3']
    def get_libraries(self):
        return ['m']
    def get_version(self, force=0, ok_status=[256,0]):
        # XXX status==256 may indicate 'unrecognized option' or
        #     'no input file'. So, version_cmd needs more work.
        return FCompiler.get_version(self,force,ok_status)

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(10)
    from numpy.distutils.fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='hpux')
    compiler.customize()
    print compiler.get_version()


# http://www.absoft.com/literature/osxuserguide.pdf
# http://www.absoft.com/documentation.html

# Notes:
# - when using -g77 then use -DUNDERSCORE_G77 to compile f2py
#   generated extension modules (works for f2py v2.45.241_1936 and up)

import os
import sys

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.fcompiler import FCompiler, dummy_fortran_file
from numpy.distutils.misc_util import cyg2win32

class AbsoftFCompiler(FCompiler):

    compiler_type = 'absoft'
    #version_pattern = r'FORTRAN 77 Compiler (?P<version>[^\s*,]*).*?Absoft Corp'
    version_pattern = r'(f90:.*?(Absoft Pro FORTRAN Version|FORTRAN 77 Compiler|Absoft Fortran Compiler Version|Copyright Absoft Corporation.*?Version))'+\
                       r' (?P<version>[^\s*,]*)(.*?Absoft Corp|)'

    # on windows: f90 -V -c dummy.f
    # f90: Copyright Absoft Corporation 1994-1998 mV2; Cray Research, Inc. 1994-1996 CF90 (2.x.x.x  f36t87) Version 2.3 Wed Apr 19, 2006  13:05:16

    # samt5735(8)$ f90 -V -c dummy.f
    # f90: Copyright Absoft Corporation 1994-2002; Absoft Pro FORTRAN Version 8.0
    # Note that fink installs g77 as f77, so need to use f90 for detection.

    executables = {
        'version_cmd'  : ["f90", "-V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':cyg2win32(dummy_fortran_file())}],
        'compiler_f77' : ["f77"],
        'compiler_fix' : ["f90"],
        'compiler_f90' : ["f90"],
        'linker_so'    : ["f90"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    if os.name=='nt':
        library_switch = '/out:'      #No space after /out:!

    module_dir_switch = None
    module_include_switch = '-p'

    def get_flags_linker_so(self):
        if os.name=='nt':
            opt = ['/dll']
        # The "-K shared" switches are being left in for pre-9.0 versions
        # of Absoft though I don't think versions earlier than 9 can
        # actually be used to build shared libraries.  In fact, version
        # 8 of Absoft doesn't recognize "-K shared" and will fail.
        elif self.get_version() >= '9.0':
            opt = ['-shared']
        else:
            opt = ["-K","shared"]
        return opt

    def library_dir_option(self, dir):
        if os.name=='nt':
            return ['-link','/PATH:"%s"' % (dir)]
        return "-L" + dir

    def library_option(self, lib):
        if os.name=='nt':
            return '%s.lib' % (lib)
        return "-l" + lib

    def get_library_dirs(self):
        opt = FCompiler.get_library_dirs(self)
        d = os.environ.get('ABSOFT')
        if d:
            if self.get_version() >= '10.0':
                # use shared libraries, the static libraries were not compiled -fPIC
                prefix = 'sh'
            else:
                prefix = ''
            if cpu.is_64bit():
                suffix = '64'
            else:
                suffix = ''
            opt.append(os.path.join(d, '%slib%s' % (prefix, suffix)))
        return opt

    def get_libraries(self):
        opt = FCompiler.get_libraries(self)
        if self.get_version() >= '10.0':
            opt.extend(['af90math', 'afio', 'af77math', 'U77'])
        elif self.get_version() >= '8.0':
            opt.extend(['f90math','fio','f77math','U77'])
        else:
            opt.extend(['fio','f90math','fmath','U77'])
        if os.name =='nt':
            opt.append('COMDLG32')
        return opt

    def get_flags(self):
        opt = FCompiler.get_flags(self)
        if os.name != 'nt':
            opt.extend(['-s'])
            if self.get_version():
                if self.get_version()>='8.2':
                    opt.append('-fpic')
        return opt

    def get_flags_f77(self):
        opt = FCompiler.get_flags_f77(self)
        opt.extend(['-N22','-N90','-N110'])
        v = self.get_version()
        if os.name == 'nt':
            if v and v>='8.0':
                opt.extend(['-f','-N15'])
        else:
            opt.append('-f')
            if v:
                if v<='4.6':
                    opt.append('-B108')
                else:
                    # Though -N15 is undocumented, it works with
                    # Absoft 8.0 on Linux
                    opt.append('-N15')
        return opt

    def get_flags_f90(self):
        opt = FCompiler.get_flags_f90(self)
        opt.extend(["-YCFRL=1","-YCOM_NAMES=LCS","-YCOM_PFX","-YEXT_PFX",
                    "-YCOM_SFX=_","-YEXT_SFX=_","-YEXT_NAMES=LCS"])
        if self.get_version():
            if self.get_version()>'4.6':
                opt.extend(["-YDEALLOC=ALL"])
        return opt

    def get_flags_fix(self):
        opt = FCompiler.get_flags_fix(self)
        opt.extend(["-YCFRL=1","-YCOM_NAMES=LCS","-YCOM_PFX","-YEXT_PFX",
                    "-YCOM_SFX=_","-YEXT_SFX=_","-YEXT_NAMES=LCS"])
        opt.extend(["-f","fixed"])
        return opt

    def get_flags_opt(self):
        opt = ['-O']
        return opt

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='absoft')
    compiler.customize()
    print compiler.get_version()

import os
import sys

from numpy.distutils.cpuinfo import cpu
from numpy.distutils.fcompiler.gnu import GnuFCompiler

class VastFCompiler(GnuFCompiler):

    compiler_type = 'vast'
    version_pattern = r'\s*Pacific-Sierra Research vf90 '\
                      '(Personal|Professional)\s+(?P<version>[^\s]*)'

    # VAST f90 does not support -o with -c. So, object files are created
    # to the current directory and then moved to build directory
    object_switch = ' && function _mvfile { mv -v `basename $1` $1 ; } && _mvfile '

    executables = {
        'version_cmd'  : ["vf90", "-v"],
        'compiler_f77' : ["g77"],
        'compiler_fix' : ["f90", "-Wv,-ya"],
        'compiler_f90' : ["f90"],
        'linker_so'    : ["f90"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }
    module_dir_switch = None  #XXX Fix me
    module_include_switch = None #XXX Fix me

    def get_version_cmd(self):
        f90 = self.compiler_f90[0]
        d,b = os.path.split(f90)
        vf90 = os.path.join(d,'v'+b)
        return vf90

    def get_flags_arch(self):
        vast_version = self.get_version()
        gnu = GnuFCompiler()
        gnu.customize()
        self.version = gnu.get_version()
        opt = GnuFCompiler.get_flags_arch(self)
        self.version = vast_version
        return opt

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from numpy.distutils.fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='vast')
    compiler.customize()
    print compiler.get_version()

import os
import sys
from distutils.command.build import build as old_build
from distutils.util import get_platform

class build(old_build):

    sub_commands = [('config_fc',     lambda *args: 1),
                    ('build_src',     old_build.has_ext_modules),
                    ] + old_build.sub_commands

    def finalize_options(self):
        build_scripts = self.build_scripts
        old_build.finalize_options(self)
        plat_specifier = ".%s-%s" % (get_platform(), sys.version[0:3])
        if build_scripts is None:
            self.build_scripts = os.path.join(self.build_base,
                                              'scripts' + plat_specifier)


import sys
from distutils.core import Command

#XXX: Implement confic_cc for enhancing C/C++ compiler options.
#XXX: Linker flags

def show_fortran_compilers(_cache=[]):
    # Using cache to prevent infinite recursion
    if _cache:
        return
    _cache.append(1)
    from numpy.distutils.fcompiler import show_fcompilers
    from numpy.distutils.core import get_distribution
    show_fcompilers(get_distribution())

class config_fc(Command):
    """ Distutils command to hold user specified options
    to Fortran compilers.

    config_fc command is used by the FCompiler.customize() method.
    """

    user_options = [
        ('fcompiler=',None,"specify Fortran compiler type"),
        ('f77exec=', None, "specify F77 compiler command"),
        ('f90exec=', None, "specify F90 compiler command"),
        ('f77flags=',None,"specify F77 compiler flags"),
        ('f90flags=',None,"specify F90 compiler flags"),
        ('opt=',None,"specify optimization flags"),
        ('arch=',None,"specify architecture specific optimization flags"),
        ('debug','g',"compile with debugging information"),
        ('noopt',None,"compile without optimization"),
        ('noarch',None,"compile without arch-dependent optimization"),
        ]

    help_options = [
        ('help-fcompiler',None, "list available Fortran compilers",
         show_fortran_compilers),
        ]

    boolean_options = ['debug','noopt','noarch']

    def initialize_options(self):
        self.fcompiler = None
        self.f77exec = None
        self.f90exec = None
        self.f77flags = None
        self.f90flags = None
        self.opt = None
        self.arch = None
        self.debug = None
        self.noopt = None
        self.noarch = None
        return

    def finalize_options(self):
        # Do nothing.
        return

    def run(self):
        # Do nothing.
        return

""" Modified version of build_ext that handles fortran source files.
"""

import os
import string
import sys
from glob import glob

from distutils.dep_util import newer_group
from distutils.command.build_ext import build_ext as old_build_ext
from distutils.errors import DistutilsFileError, DistutilsSetupError
from distutils.file_util import copy_file

from numpy.distutils import log
from numpy.distutils.exec_command import exec_command
from numpy.distutils.system_info import combine_paths
from numpy.distutils.misc_util import filter_sources, has_f_sources, \
     has_cxx_sources, get_ext_source_files, all_strings, \
     get_numpy_include_dirs, is_sequence


class build_ext (old_build_ext):

    description = "build C/C++/F extensions (compile/link to build directory)"

    user_options = old_build_ext.user_options + [
        ('fcompiler=', None,
         "specify the Fortran compiler type"),
        ]

    def initialize_options(self):
        old_build_ext.initialize_options(self)
        self.fcompiler = None
        return

    def finalize_options(self):
        incl_dirs = self.include_dirs
        old_build_ext.finalize_options(self)
        if incl_dirs is not None:
            self.include_dirs.extend(self.distribution.include_dirs or [])
        self.set_undefined_options('config_fc',
                                   ('fcompiler', 'fcompiler'))
        return

    def run(self):
        if not self.extensions:
            return

        # Make sure that extension sources are complete.
        for ext in self.extensions:
            if not all_strings(ext.sources):
                self.run_command('build_src')

        if self.distribution.has_c_libraries():
            build_clib = self.get_finalized_command('build_clib')
            self.library_dirs.append(build_clib.build_clib)
        else:
            build_clib = None

        # Not including C libraries to the list of
        # extension libraries automatically to prevent
        # bogus linking commands. Extensions must
        # explicitly specify the C libraries that they use.

        # Determine if Fortran compiler is needed.
        if build_clib and build_clib.fcompiler is not None:
            need_f_compiler = 1
        else:
            need_f_compiler = 0
            for ext in self.extensions:
                if has_f_sources(ext.sources):
                    need_f_compiler = 1
                    break
                if getattr(ext,'language','c') in ['f77','f90']:
                    need_f_compiler = 1
                    break

        # Determine if C++ compiler is needed.
        need_cxx_compiler = 0
        for ext in self.extensions:
            if has_cxx_sources(ext.sources):
                need_cxx_compiler = 1
                break
            if getattr(ext,'language','c')=='c++':
                need_cxx_compiler = 1
                break

        from distutils.ccompiler import new_compiler
        self.compiler = new_compiler(compiler=self.compiler,
                                     verbose=self.verbose,
                                     dry_run=self.dry_run,
                                     force=self.force)
        self.compiler.customize(self.distribution,need_cxx=need_cxx_compiler)
        self.compiler.customize_cmd(self)
        self.compiler.show_customization()

        # Initialize Fortran/C++ compilers if needed.
        if need_f_compiler:
            from numpy.distutils.fcompiler import new_fcompiler
            self.fcompiler = new_fcompiler(compiler=self.fcompiler,
                                           verbose=self.verbose,
                                           dry_run=self.dry_run,
                                           force=self.force)
            if self.fcompiler.get_version():
                self.fcompiler.customize(self.distribution)
                self.fcompiler.customize_cmd(self)
                self.fcompiler.show_customization()
            else:
                self.warn('fcompiler=%s is not available.' % (self.fcompiler.compiler_type))
                self.fcompiler = None

        # Build extensions
        self.build_extensions()
        return

    def swig_sources(self, sources):
        # Do nothing. Swig sources have beed handled in build_src command.
        return sources

    def build_extension(self, ext):
        sources = ext.sources
        if sources is None or not is_sequence(sources):
            raise DistutilsSetupError, \
                  ("in 'ext_modules' option (extension '%s'), " +
                   "'sources' must be present and must be " +
                   "a list of source filenames") % ext.name
        sources = list(sources)

        if not sources:
            return

        fullname = self.get_ext_fullname(ext.name)
        if self.inplace:
            modpath = string.split(fullname, '.')
            package = string.join(modpath[0:-1], '.')
            base = modpath[-1]

            build_py = self.get_finalized_command('build_py')
            package_dir = build_py.get_package_dir(package)
            ext_filename = os.path.join(package_dir,
                                        self.get_ext_filename(base))
        else:
            ext_filename = os.path.join(self.build_lib,
                                        self.get_ext_filename(fullname))
        depends = sources + ext.depends

        if not (self.force or newer_group(depends, ext_filename, 'newer')):
            log.debug("skipping '%s' extension (up-to-date)", ext.name)
            return
        else:
            log.info("building '%s' extension", ext.name)

        extra_args = ext.extra_compile_args or []
        macros = ext.define_macros[:]
        for undef in ext.undef_macros:
            macros.append((undef,))

        clib_libraries = []
        clib_library_dirs = []
        if self.distribution.libraries:
            for libname,build_info in self.distribution.libraries:
                if libname in ext.libraries:
                    macros.extend(build_info.get('macros',[]))
                    clib_libraries.extend(build_info.get('libraries',[]))
                    clib_library_dirs.extend(build_info.get('library_dirs',[]))

        c_sources, cxx_sources, f_sources, fmodule_sources = \
                   filter_sources(ext.sources)
        if self.compiler.compiler_type=='msvc':
            if cxx_sources:
                # Needed to compile kiva.agg._agg extension.
                extra_args.append('/Zm1000')
            # this hack works around the msvc compiler attributes
            # problem, msvc uses its own convention :(
            c_sources += cxx_sources
            cxx_sources = []


        kws = {'depends':ext.depends}
        output_dir = self.build_temp

        include_dirs = ext.include_dirs + get_numpy_include_dirs()

        c_objects = []
        if c_sources:
            log.info("compiling C sources")
            c_objects = self.compiler.compile(c_sources,
                                              output_dir=output_dir,
                                              macros=macros,
                                              include_dirs=include_dirs,
                                              debug=self.debug,
                                              extra_postargs=extra_args,
                                              **kws)
        if cxx_sources:
            log.info("compiling C++ sources")

            old_compiler = self.compiler.compiler_so[0]
            self.compiler.compiler_so[0] = self.compiler.compiler_cxx[0]

            c_objects += self.compiler.compile(cxx_sources,
                                              output_dir=output_dir,
                                              macros=macros,
                                              include_dirs=include_dirs,
                                              debug=self.debug,
                                              extra_postargs=extra_args,
                                              **kws)
            self.compiler.compiler_so[0] = old_compiler

        check_for_f90_modules = not not fmodule_sources

        if f_sources or fmodule_sources:
            extra_postargs = []
            module_dirs = ext.module_dirs[:]

            #if self.fcompiler.compiler_type=='ibm':
            macros = []

            if check_for_f90_modules:
                module_build_dir = os.path.join(\
                    self.build_temp,os.path.dirname(\
                    self.get_ext_filename(fullname)))

                self.mkpath(module_build_dir)
                if self.fcompiler.module_dir_switch is None:
                    existing_modules = glob('*.mod')
                extra_postargs += self.fcompiler.module_options(\
                    module_dirs,module_build_dir)

            f_objects = []
            if fmodule_sources:
                log.info("compiling Fortran 90 module sources")
                f_objects = self.fcompiler.compile(fmodule_sources,
                                                   output_dir=self.build_temp,
                                                   macros=macros,
                                                   include_dirs=include_dirs,
                                                   debug=self.debug,
                                                   extra_postargs=extra_postargs,
                                                   depends=ext.depends)

            if check_for_f90_modules \
                   and self.fcompiler.module_dir_switch is None:
                for f in glob('*.mod'):
                    if f in existing_modules:
                        continue
                    try:
                        self.move_file(f, module_build_dir)
                    except DistutilsFileError:  # already exists in destination
                        os.remove(f)

            if f_sources:
                log.info("compiling Fortran sources")
                f_objects += self.fcompiler.compile(f_sources,
                                                    output_dir=self.build_temp,
                                                    macros=macros,
                                                    include_dirs=include_dirs,
                                                    debug=self.debug,
                                                    extra_postargs=extra_postargs,
                                                    depends=ext.depends)
        else:
            f_objects = []

        objects = c_objects + f_objects

        if ext.extra_objects:
            objects.extend(ext.extra_objects)
        extra_args = ext.extra_link_args or []

        try:
            old_linker_so_0 = self.compiler.linker_so[0]
        except:
            pass

        use_fortran_linker = getattr(ext,'language','c') in ['f77','f90'] \
                             and self.fcompiler is not None
        c_libraries = []
        c_library_dirs = []
        if use_fortran_linker or f_sources:
            use_fortran_linker = 1
        elif self.distribution.has_c_libraries():
            build_clib = self.get_finalized_command('build_clib')
            f_libs = []
            for (lib_name, build_info) in build_clib.libraries:
                if has_f_sources(build_info.get('sources',[])):
                    f_libs.append(lib_name)
                if lib_name in ext.libraries:
                    # XXX: how to determine if c_libraries contain
                    # fortran compiled sources?
                    c_libraries.extend(build_info.get('libraries',[]))
                    c_library_dirs.extend(build_info.get('library_dirs',[]))
            for l in ext.libraries:
                if l in f_libs:
                    use_fortran_linker = 1
                    break

        # Always use system linker when using MSVC compiler.
        if self.compiler.compiler_type=='msvc' and use_fortran_linker:
            self._libs_with_msvc_and_fortran(c_libraries, c_library_dirs)
            use_fortran_linker = False

        if use_fortran_linker:
            if cxx_sources:
                # XXX: Which linker should be used, Fortran or C++?
                log.warn('mixing Fortran and C++ is untested')
            link = self.fcompiler.link_shared_object
            language = ext.language or self.fcompiler.detect_language(f_sources)
        else:
            link = self.compiler.link_shared_object
            if sys.version[:3]>='2.3':
                language = ext.language or self.compiler.detect_language(sources)
            else:
                language = ext.language
            if cxx_sources:
                self.compiler.linker_so[0] = self.compiler.compiler_cxx[0]

        if sys.version[:3]>='2.3':
            kws = {'target_lang':language}
        else:
            kws = {}

        link(objects, ext_filename,
             libraries=self.get_libraries(ext) + c_libraries + clib_libraries,
             library_dirs=ext.library_dirs + c_library_dirs + clib_library_dirs,
             runtime_library_dirs=ext.runtime_library_dirs,
             extra_postargs=extra_args,
             export_symbols=self.get_export_symbols(ext),
             debug=self.debug,
             build_temp=self.build_temp,**kws)

        try:
            self.compiler.linker_so[0] = old_linker_so_0
        except:
            pass

        return

    def _libs_with_msvc_and_fortran(self, c_libraries, c_library_dirs):
        # Always use system linker when using MSVC compiler.
        f_lib_dirs = []
        for dir in self.fcompiler.library_dirs:
            # correct path when compiling in Cygwin but with normal Win
            # Python
            if dir.startswith('/usr/lib'):
                s,o = exec_command(['cygpath', '-w', dir], use_tee=False)
                if not s:
                    dir = o
            f_lib_dirs.append(dir)
        c_library_dirs.extend(f_lib_dirs)

        # make g77-compiled static libs available to MSVC
        lib_added = False
        for lib in self.fcompiler.libraries:
            if not lib.startswtih('msvcr'):
                c_libraries.append(lib)
                p = combine_paths(f_lib_dirs, 'lib' + lib + '.a')
                if p:
                    dst_name = os.path.join(self.build_temp, lib + '.lib')
                    copy_file(p[0], dst_name)
                    if not lib_added:
                        c_library_dirs.append(self.build_temp)
                        lib_added = True

    def get_source_files (self):
        self.check_extensions_list(self.extensions)
        filenames = []
        for ext in self.extensions:
            filenames.extend(get_ext_source_files(ext))
        return filenames

    def get_outputs (self):
        self.check_extensions_list(self.extensions)

        outputs = []
        for ext in self.extensions:
            if not ext.sources:
                continue
            fullname = self.get_ext_fullname(ext.name)
            outputs.append(os.path.join(self.build_lib,
                                        self.get_ext_filename(fullname)))
        return outputs

# Added Fortran compiler support to config. Currently useful only for
# try_compile call. try_run works but is untested for most of Fortran
# compilers (they must define linker_exe first).
# Pearu Peterson

import os, signal
from distutils.command.config import config as old_config
from distutils.command.config import LANG_EXT
from distutils import log
from numpy.distutils.exec_command import exec_command

LANG_EXT['f77'] = '.f'
LANG_EXT['f90'] = '.f90'

class config(old_config):
    old_config.user_options += [
        ('fcompiler=', None,
         "specify the Fortran compiler type"),
        ]

    def initialize_options(self):
        self.fcompiler = None
        old_config.initialize_options(self)
        return

    def finalize_options(self):
        old_config.finalize_options(self)
        f = self.distribution.get_command_obj('config_fc')
        self.set_undefined_options('config_fc',
                                   ('fcompiler', 'fcompiler'))
        return

    def _check_compiler (self):
        old_config._check_compiler(self)
        from numpy.distutils.fcompiler import FCompiler, new_fcompiler
        if not isinstance(self.fcompiler, FCompiler):
            self.fcompiler = new_fcompiler(compiler=self.fcompiler,
                                           dry_run=self.dry_run, force=1)
            self.fcompiler.customize(self.distribution)
            self.fcompiler.customize_cmd(self)
            self.fcompiler.show_customization()
        return

    def _wrap_method(self,mth,lang,args):
        from distutils.ccompiler import CompileError
        from distutils.errors import DistutilsExecError
        save_compiler = self.compiler
        if lang in ['f77','f90']:
            self.compiler = self.fcompiler
        try:
            ret = mth(*((self,)+args))
        except (DistutilsExecError,CompileError),msg:
            self.compiler = save_compiler
            raise CompileError
        self.compiler = save_compiler
        return ret

    def _compile (self, body, headers, include_dirs, lang):
        return self._wrap_method(old_config._compile,lang,
                                 (body, headers, include_dirs, lang))

    def _link (self, body,
               headers, include_dirs,
               libraries, library_dirs, lang):
        return self._wrap_method(old_config._link,lang,
                                 (body, headers, include_dirs,
                                  libraries, library_dirs, lang))

    def check_func(self, func,
                   headers=None, include_dirs=None,
                   libraries=None, library_dirs=None,
                   decl=False, call=False, call_args=None):
        # clean up distutils's config a bit: add void to main(), and
        # return a value.
        self._check_compiler()
        body = []
        if decl:
            body.append("int %s ();" % func)
        body.append("int main (void) {")
        if call:
            if call_args is None:
                call_args = ''
            body.append("  %s(%s);" % (func, call_args))
        else:
            body.append("  %s;" % func)
        body.append("  return 0;")
        body.append("}")
        body = '\n'.join(body) + "\n"

        return self.try_link(body, headers, include_dirs,
                             libraries, library_dirs)

    def get_output(self, body, headers=None, include_dirs=None,
                   libraries=None, library_dirs=None,
                   lang="c"):
        """Try to compile, link to an executable, and run a program
        built from 'body' and 'headers'. Returns the exit status code
        of the program and its output.
        """
        from distutils.ccompiler import CompileError, LinkError
        self._check_compiler()
        exitcode, output = 255, ''
        try:
            src, obj, exe = self._link(body, headers, include_dirs,
                                       libraries, library_dirs, lang)
            exe = os.path.join('.', exe)
            exitstatus, output = exec_command(exe, execute_in='.')
            if hasattr(os, 'WEXITSTATUS'):
                exitcode = os.WEXITSTATUS(exitstatus)
                if os.WIFSIGNALED(exitstatus):
                    sig = os.WTERMSIG(exitstatus)
                    log.error('subprocess exited with signal %d' % (sig,))
                    if sig == signal.SIGINT:
                        # control-C
                        raise KeyboardInterrupt
            else:
                exitcode = exitstatus
            log.info("success!")
        except (CompileError, LinkError):
            log.info("failure.")

        self._clean()
        return exitcode, output


import os
from distutils.command.install_headers import install_headers as old_install_headers

class install_headers (old_install_headers):

    def run (self):
        headers = self.distribution.headers
        if not headers:
            return

        prefix = os.path.dirname(self.install_dir)
        for header in headers:
            if isinstance(header,tuple):
                # Kind of a hack, but I don't know where else to change this...
                if header[0] == 'numpy.core':
                    header = ('numpy', header[1])
                    if os.path.splitext(header[1])[1] == '.inc':
                        continue
                d = os.path.join(*([prefix]+header[0].split('.')))
                header = header[1]
            else:
                d = self.install_dir
            self.mkpath(d)
            (out, _) = self.copy_file(header, d)
            self.outfiles.append(out)


from distutils.command.build_py import build_py as old_build_py
from numpy.distutils.misc_util import is_string

class build_py(old_build_py):

    def find_package_modules(self, package, package_dir):
        modules = old_build_py.find_package_modules(self, package, package_dir)

        # Find build_src generated *.py files.
        build_src = self.get_finalized_command('build_src')
        modules += build_src.py_modules_dict.get(package,[])

        return modules

    def find_modules(self):
        old_py_modules = self.py_modules[:]
        new_py_modules = filter(is_string, self.py_modules)
        self.py_modules[:] = new_py_modules
        modules = old_build_py.find_modules(self)
        self.py_modules[:] = old_py_modules
        return modules

    # XXX: Fix find_source_files for item in py_modules such that item is 3-tuple
    # and item[2] is source file.

""" Build swig, f2py, weave, sources.
"""

import os
import re
import sys

from distutils.command import build_ext
from distutils.dep_util import newer_group, newer
from distutils.util import get_platform

from numpy.distutils import log
from numpy.distutils.misc_util import fortran_ext_match, \
     appendpath, is_string, is_sequence
from numpy.distutils.from_template import process_file as process_f_file
from numpy.distutils.conv_template import process_file as process_c_file

class build_src(build_ext.build_ext):

    description = "build sources from SWIG, F2PY files or a function"

    user_options = [
        ('build-src=', 'd', "directory to \"build\" sources to"),
        ('f2pyflags=', None, "additonal flags to f2py"),
        ('swigflags=', None, "additional flags to swig"),
        ('force', 'f', "forcibly build everything (ignore file timestamps)"),
        ('inplace', 'i',
         "ignore build-lib and put compiled extensions into the source " +
         "directory alongside your pure Python modules"),
        ]

    boolean_options = ['force','inplace']

    help_options = []

    def initialize_options(self):
        self.extensions = None
        self.package = None
        self.py_modules = None
        self.py_modules_dict = None
        self.build_src = None
        self.build_lib = None
        self.build_base = None
        self.force = None
        self.inplace = None
        self.package_dir = None
        self.f2pyflags = None
        self.swigflags = None
        return

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_base', 'build_base'),
                                   ('build_lib', 'build_lib'),
                                   ('force', 'force'))
        if self.package is None:
            self.package = self.distribution.ext_package
        self.extensions = self.distribution.ext_modules
        self.libraries = self.distribution.libraries or []
        self.py_modules = self.distribution.py_modules or []
        self.data_files = self.distribution.data_files or []

        if self.build_src is None:
            plat_specifier = ".%s-%s" % (get_platform(), sys.version[0:3])
            self.build_src = os.path.join(self.build_base, 'src'+plat_specifier)
        if self.inplace is None:
            build_ext = self.get_finalized_command('build_ext')
            self.inplace = build_ext.inplace

        # py_modules_dict is used in build_py.find_package_modules
        self.py_modules_dict = {}

        if self.f2pyflags is None:
            self.f2pyflags = []
        else:
            self.f2pyflags = self.f2pyflags.split() # XXX spaces??

        if self.swigflags is None:
            self.swigflags = []
        else:
            self.swigflags = self.swigflags.split() # XXX spaces??
        return

    def run(self):
        if not (self.extensions or self.libraries):
            return
        self.build_sources()

        return

    def build_sources(self):

        if self.inplace:
            self.get_package_dir = self.get_finalized_command('build_py')\
                                   .get_package_dir

        self.build_py_modules_sources()

        for libname_info in self.libraries:
            self.build_library_sources(*libname_info)

        if self.extensions:
            self.check_extensions_list(self.extensions)

            for ext in self.extensions:
                self.build_extension_sources(ext)

        self.build_data_files_sources()

        return

    def build_data_files_sources(self):
        if not self.data_files:
            return
        log.info('building data_files sources')
        from numpy.distutils.misc_util import get_data_files
        new_data_files = []
        for data in self.data_files:
            if isinstance(data,str):
                new_data_files.append(data)
            elif isinstance(data,tuple):
                d,files = data
                if self.inplace:
                    build_dir = self.get_package_dir('.'.join(d.split(os.sep)))
                else:
                    build_dir = os.path.join(self.build_src,d)
                funcs = filter(callable,files)
                files = filter(lambda f:not callable(f), files)
                for f in funcs:
                    if f.func_code.co_argcount==1:
                        s = f(build_dir)
                    else:
                        s = f()
                    if s is not None:
                        if isinstance(s,list):
                            files.extend(s)
                        elif isinstance(s,str):
                            files.append(s)
                        else:
                            raise TypeError(repr(s))
                filenames = get_data_files((d,files))
                new_data_files.append((d, filenames))
            else:
                raise
        self.data_files[:] = new_data_files
        return

    def build_py_modules_sources(self):
        if not self.py_modules:
            return
        log.info('building py_modules sources')
        new_py_modules = []
        for source in self.py_modules:
            if is_sequence(source) and len(source)==3:
                package, module_base, source = source
                if self.inplace:
                    build_dir = self.get_package_dir(package)
                else:
                    build_dir = os.path.join(self.build_src,
                                             os.path.join(*package.split('.')))
                if callable(source):
                    target = os.path.join(build_dir, module_base + '.py')
                    source = source(target)
                if source is None:
                    continue
                modules = [(package, module_base, source)]
                if not self.py_modules_dict.has_key(package):
                    self.py_modules_dict[package] = []
                self.py_modules_dict[package] += modules
            else:
                new_py_modules.append(source)
        self.py_modules[:] = new_py_modules
        return

    def build_library_sources(self, lib_name, build_info):
        sources = list(build_info.get('sources',[]))

        if not sources:
            return

        log.info('building library "%s" sources' % (lib_name))

        sources = self.generate_sources(sources, (lib_name, build_info))

        sources = self.template_sources(sources, (lib_name, build_info))

        sources, h_files = self.filter_h_files(sources)

        if h_files:
            print self.package,'- nothing done with h_files=',h_files

        #for f in h_files:
        #    self.distribution.headers.append((lib_name,f))

        build_info['sources'] = sources
        return

    def build_extension_sources(self, ext):

        sources = list(ext.sources)

        log.info('building extension "%s" sources' % (ext.name))

        fullname = self.get_ext_fullname(ext.name)

        modpath = fullname.split('.')
        package = '.'.join(modpath[0:-1])

        if self.inplace:
            self.ext_target_dir = self.get_package_dir(package)

        sources = self.generate_sources(sources, ext)

        sources = self.template_sources(sources, ext)

        sources = self.swig_sources(sources, ext)

        sources = self.f2py_sources(sources, ext)

        sources = self.pyrex_sources(sources, ext)

        sources, py_files = self.filter_py_files(sources)

        if not self.py_modules_dict.has_key(package):
            self.py_modules_dict[package] = []
        modules = []
        for f in py_files:
            module = os.path.splitext(os.path.basename(f))[0]
            modules.append((package, module, f))
        self.py_modules_dict[package] += modules

        sources, h_files = self.filter_h_files(sources)

        if h_files:
            print package,'- nothing done with h_files=',h_files
        #for f in h_files:
        #    self.distribution.headers.append((package,f))

        ext.sources = sources

        return

    def generate_sources(self, sources, extension):
        new_sources = []
        func_sources = []
        for source in sources:
            if is_string(source):
                new_sources.append(source)
            else:
                func_sources.append(source)
        if not func_sources:
            return new_sources
        if self.inplace and not is_sequence(extension):
            build_dir = self.ext_target_dir
        else:
            if is_sequence(extension):
                name = extension[0]
            #    if not extension[1].has_key('include_dirs'):
            #        extension[1]['include_dirs'] = []
            #    incl_dirs = extension[1]['include_dirs']
            else:
                name = extension.name
            #    incl_dirs = extension.include_dirs
            #if self.build_src not in incl_dirs:
            #    incl_dirs.append(self.build_src)
            build_dir = os.path.join(*([self.build_src]\
                                       +name.split('.')[:-1]))
        self.mkpath(build_dir)
        for func in func_sources:
            source = func(extension, build_dir)
            if not source:
                continue
            if is_sequence(source):
                [log.info("  adding '%s' to sources." % (s,)) for s in source]
                new_sources.extend(source)
            else:
                log.info("  adding '%s' to sources." % (source,))
                new_sources.append(source)

        return new_sources

    def filter_py_files(self, sources):
        return self.filter_files(sources,['.py'])

    def filter_h_files(self, sources):
        return self.filter_files(sources,['.h','.hpp','.inc'])

    def filter_files(self, sources, exts = []):
        new_sources = []
        files = []
        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext in exts:
                files.append(source)
            else:
                new_sources.append(source)
        return new_sources, files

    def template_sources(self, sources, extension):
        new_sources = []
        if is_sequence(extension):
            depends = extension[1].get('depends')
            include_dirs = extension[1].get('include_dirs')
        else:
            depends = extension.depends
            include_dirs = extension.include_dirs
        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext == '.src':  # Template file
                if self.inplace:
                    target_dir = os.path.dirname(base)
                else:
                    target_dir = appendpath(self.build_src, os.path.dirname(base))
                self.mkpath(target_dir)
                target_file = os.path.join(target_dir,os.path.basename(base))
                if (self.force or newer_group([source] + depends, target_file)):
                    if _f_pyf_ext_match(base):
                        log.info("from_template:> %s" % (target_file))
                        outstr = process_f_file(source)
                    else:
                        log.info("conv_template:> %s" % (target_file))
                        outstr = process_c_file(source)
                    fid = open(target_file,'w')
                    fid.write(outstr)
                    fid.close()
                if _header_ext_match(target_file):
                    d = os.path.dirname(target_file)
                    if d not in include_dirs:
                        log.info("  adding '%s' to include_dirs." % (d))
                        include_dirs.append(d)
                new_sources.append(target_file)
            else:
                new_sources.append(source)
        return new_sources

    def pyrex_sources(self, sources, extension):
        have_pyrex = False
        try:
            import Pyrex
            have_pyrex = True
        except ImportError:
            pass
        new_sources = []
        ext_name = extension.name.split('.')[-1]
        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext == '.pyx':
                if self.inplace or not have_pyrex:
                    target_dir = os.path.dirname(base)
                else:
                    target_dir = appendpath(self.build_src, os.path.dirname(base))
                target_file = os.path.join(target_dir, ext_name + '.c')
                depends = [source] + extension.depends
                if (self.force or newer_group(depends, target_file, 'newer')):
                    if have_pyrex:
                        log.info("pyrexc:> %s" % (target_file))
                        self.mkpath(target_dir)
                        from Pyrex.Compiler import Main
                        options = Main.CompilationOptions(
                            defaults=Main.default_options,
                            output_file=target_file)
                        pyrex_result = Main.compile(source, options=options)
                        if pyrex_result.num_errors != 0:
                            raise RuntimeError("%d errors in Pyrex compile" %
                                               pyrex_result.num_errors)
                    else:
                        log.warn("Pyrex needed to compile %s but not available."\
                                 " Using old target %s"\
                                 % (source, target_file))
                new_sources.append(target_file)
            else:
                new_sources.append(source)
        return new_sources

    def f2py_sources(self, sources, extension):
        new_sources = []
        f2py_sources = []
        f_sources = []
        f2py_targets = {}
        target_dirs = []
        ext_name = extension.name.split('.')[-1]
        skip_f2py = 0

        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext == '.pyf': # F2PY interface file
                if self.inplace:
                    target_dir = os.path.dirname(base)
                else:
                    target_dir = appendpath(self.build_src, os.path.dirname(base))
                if os.path.isfile(source):
                    name = get_f2py_modulename(source)
                    if name != ext_name:
                        raise ValueError('mismatch of extension names: %s '
                                         'provides %r but expected %r' % (
                                          source, name, ext_name))
                    target_file = os.path.join(target_dir,name+'module.c')
                else:
                    log.debug('  source %s does not exist: skipping f2py\'ing.' \
                              % (source))
                    name = ext_name
                    skip_f2py = 1
                    target_file = os.path.join(target_dir,name+'module.c')
                    if not os.path.isfile(target_file):
                        log.debug('  target %s does not exist:\n   '\
                                  'Assuming %smodule.c was generated with '\
                                  '"build_src --inplace" command.' \
                                  % (target_file, name))
                        target_dir = os.path.dirname(base)
                        target_file = os.path.join(target_dir,name+'module.c')
                        if not os.path.isfile(target_file):
                            raise ValueError("%r missing" % (target_file,))
                        log.debug('   Yes! Using %s as up-to-date target.' \
                                  % (target_file))
                target_dirs.append(target_dir)
                f2py_sources.append(source)
                f2py_targets[source] = target_file
                new_sources.append(target_file)
            elif fortran_ext_match(ext):
                f_sources.append(source)
            else:
                new_sources.append(source)

        if not (f2py_sources or f_sources):
            return new_sources

        map(self.mkpath, target_dirs)

        f2py_options = extension.f2py_options + self.f2pyflags

        if self.distribution.libraries:
            for name,build_info in self.distribution.libraries:
                if name in extension.libraries:
                    f2py_options.extend(build_info.get('f2py_options',[]))

        log.info("f2py options: %s" % (f2py_options))

        if f2py_sources:
            if len(f2py_sources) != 1:
                raise ValueError(
                    'only one .pyf file is allowed per extension module but got'\
                    ' more: %r' % (f2py_sources,))
            source = f2py_sources[0]
            target_file = f2py_targets[source]
            target_dir = os.path.dirname(target_file) or '.'
            depends = [source] + extension.depends
            if (self.force or newer_group(depends, target_file,'newer')) \
                   and not skip_f2py:
                log.info("f2py: %s" % (source))
                import numpy.f2py as f2py2e
                f2py2e.run_main(f2py_options + ['--build-dir',target_dir,source])
            else:
                log.debug("  skipping '%s' f2py interface (up-to-date)" % (source))
        else:
            #XXX TODO: --inplace support for sdist command
            if is_sequence(extension):
                name = extension[0]
            else: name = extension.name
            target_dir = os.path.join(*([self.build_src]\
                                        +name.split('.')[:-1]))
            target_file = os.path.join(target_dir,ext_name + 'module.c')
            new_sources.append(target_file)
            depends = f_sources + extension.depends
            if (self.force or newer_group(depends, target_file, 'newer')) \
                   and not skip_f2py:
                import numpy.f2py as f2py2e
                log.info("f2py:> %s" % (target_file))
                self.mkpath(target_dir)
                f2py2e.run_main(f2py_options + ['--lower',
                                                '--build-dir',target_dir]+\
                                ['-m',ext_name]+f_sources)
            else:
                log.debug("  skipping f2py fortran files for '%s' (up-to-date)"\
                          % (target_file))

        if not os.path.isfile(target_file):
            raise ValueError("%r missing" % (target_file,))

        target_c = os.path.join(self.build_src,'fortranobject.c')
        target_h = os.path.join(self.build_src,'fortranobject.h')
        log.info("  adding '%s' to sources." % (target_c))
        new_sources.append(target_c)
        if self.build_src not in extension.include_dirs:
            log.info("  adding '%s' to include_dirs." \
                     % (self.build_src))
            extension.include_dirs.append(self.build_src)

        if not skip_f2py:
            import numpy.f2py as f2py2e
            d = os.path.dirname(f2py2e.__file__)
            source_c = os.path.join(d,'src','fortranobject.c')
            source_h = os.path.join(d,'src','fortranobject.h')
            if newer(source_c,target_c) or newer(source_h,target_h):
                self.mkpath(os.path.dirname(target_c))
                self.copy_file(source_c,target_c)
                self.copy_file(source_h,target_h)
        else:
            if not os.path.isfile(target_c):
                raise ValueError("%r missing" % (target_c,))
            if not os.path.isfile(target_h):
                raise ValueError("%r missing" % (target_h,))

        for name_ext in ['-f2pywrappers.f','-f2pywrappers2.f90']:
            filename = os.path.join(target_dir,ext_name + name_ext)
            if os.path.isfile(filename):
                log.info("  adding '%s' to sources." % (filename))
                f_sources.append(filename)

        return new_sources + f_sources

    def swig_sources(self, sources, extension):
        # Assuming SWIG 1.3.14 or later. See compatibility note in
        #   http://www.swig.org/Doc1.3/Python.html#Python_nn6

        new_sources = []
        swig_sources = []
        swig_targets = {}
        target_dirs = []
        py_files = []     # swig generated .py files
        target_ext = '.c'
        typ = None
        is_cpp = 0
        skip_swig = 0
        ext_name = extension.name.split('.')[-1]

        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext == '.i': # SWIG interface file
                if self.inplace:
                    target_dir = os.path.dirname(base)
                    py_target_dir = self.ext_target_dir
                else:
                    target_dir = appendpath(self.build_src, os.path.dirname(base))
                    py_target_dir = target_dir
                if os.path.isfile(source):
                    name = get_swig_modulename(source)
                    if name != ext_name[1:]:
                        raise ValueError(
                            'mismatch of extension names: %s provides %r'
                            ' but expected %r' % (source, name, ext_name[1:]))
                    if typ is None:
                        typ = get_swig_target(source)
                        is_cpp = typ=='c++'
                        if is_cpp:
                            target_ext = '.cpp'
                    else:
                        assert typ == get_swig_target(source), repr(typ)
                    target_file = os.path.join(target_dir,'%s_wrap%s' \
                                               % (name, target_ext))
                else:
                    log.debug('  source %s does not exist: skipping swig\'ing.' \
                             % (source))
                    name = ext_name[1:]
                    skip_swig = 1
                    target_file = _find_swig_target(target_dir, name)
                    if not os.path.isfile(target_file):
                        log.debug('  target %s does not exist:\n   '\
                                  'Assuming %s_wrap.{c,cpp} was generated with '\
                                  '"build_src --inplace" command.' \
                                 % (target_file, name))
                        target_dir = os.path.dirname(base)
                        target_file = _find_swig_target(target_dir, name)
                        if not os.path.isfile(target_file):
                            raise ValueError("%r missing" % (target_file,))
                        log.debug('   Yes! Using %s as up-to-date target.' \
                                  % (target_file))
                target_dirs.append(target_dir)
                new_sources.append(target_file)
                py_files.append(os.path.join(py_target_dir, name+'.py'))
                swig_sources.append(source)
                swig_targets[source] = new_sources[-1]
            else:
                new_sources.append(source)

        if not swig_sources:
            return new_sources

        if skip_swig:
            return new_sources + py_files

        map(self.mkpath, target_dirs)
        swig = self.find_swig()
        swig_cmd = [swig, "-python"]
        if is_cpp:
            swig_cmd.append('-c++')
        for d in extension.include_dirs:
            swig_cmd.append('-I'+d)
        for source in swig_sources:
            target = swig_targets[source]
            depends = [source] + extension.depends
            if self.force or newer_group(depends, target, 'newer'):
                log.info("%s: %s" % (os.path.basename(swig) \
                                     + (is_cpp and '++' or ''), source))
                self.spawn(swig_cmd + self.swigflags \
                           + ["-o", target, '-outdir', py_target_dir, source])
            else:
                log.debug("  skipping '%s' swig interface (up-to-date)" \
                         % (source))

        return new_sources + py_files

_f_pyf_ext_match = re.compile(r'.*[.](f90|f95|f77|for|ftn|f|pyf)\Z',re.I).match
_header_ext_match = re.compile(r'.*[.](inc|h|hpp)\Z',re.I).match

#### SWIG related auxiliary functions ####
_swig_module_name_match = re.compile(r'\s*%module\s*(.*\(\s*package\s*=\s*"(?P<package>[\w_]+)".*\)|)\s*(?P<name>[\w_]+)',
                                     re.I).match
_has_c_header = re.compile(r'-[*]-\s*c\s*-[*]-',re.I).search
_has_cpp_header = re.compile(r'-[*]-\s*c[+][+]\s*-[*]-',re.I).search

def get_swig_target(source):
    f = open(source,'r')
    result = 'c'
    line = f.readline()
    if _has_cpp_header(line):
        result = 'c++'
    if _has_c_header(line):
        result = 'c'
    f.close()
    return result

def get_swig_modulename(source):
    f = open(source,'r')
    f_readlines = getattr(f,'xreadlines',f.readlines)
    name = None
    for line in f_readlines():
        m = _swig_module_name_match(line)
        if m:
            name = m.group('name')
            break
    f.close()
    return name

def _find_swig_target(target_dir,name):
    for ext in ['.cpp','.c']:
        target = os.path.join(target_dir,'%s_wrap%s' % (name, ext))
        if os.path.isfile(target):
            break
    return target

#### F2PY related auxiliary functions ####

_f2py_module_name_match = re.compile(r'\s*python\s*module\s*(?P<name>[\w_]+)',
                                re.I).match
_f2py_user_module_name_match = re.compile(r'\s*python\s*module\s*(?P<name>[\w_]*?'\
                                     '__user__[\w_]*)',re.I).match

def get_f2py_modulename(source):
    name = None
    f = open(source)
    f_readlines = getattr(f,'xreadlines',f.readlines)
    for line in f_readlines():
        m = _f2py_module_name_match(line)
        if m:
            if _f2py_user_module_name_match(line): # skip *__user__* names
                continue
            name = m.group('name')
            break
    f.close()
    return name

##########################################

"""distutils.command

Package containing implementation of all the standard Distutils
commands."""

__revision__ = "$Id: __init__.py,v 1.3 2005/05/16 11:08:49 pearu Exp $"

distutils_all = [  'build_py',
                   'clean',
                   'install_lib',
                   'install_scripts',
                   'bdist',
                   'bdist_dumb',
                   'bdist_wininst',
                ]

__import__('distutils.command',globals(),locals(),distutils_all)

__all__ = ['build',
           'config_compiler',
           'config',
           'build_src',
           'build_ext',
           'build_clib',
           'build_scripts',
           'install',
           'install_data',
           'install_headers',
           'bdist_rpm',
           'sdist',
          ] + distutils_all

from distutils.command.sdist import sdist as old_sdist
from numpy.distutils.misc_util import get_data_files

class sdist(old_sdist):

    def add_defaults (self):
        old_sdist.add_defaults(self)

        dist = self.distribution

        if dist.has_data_files():
            for data in dist.data_files:
                self.filelist.extend(get_data_files(data))

        if dist.has_headers():
            headers = []
            for h in dist.headers:
                if isinstance(h,str): headers.append(h)
                else: headers.append(h[1])
            self.filelist.extend(headers)

        return

""" Modified version of build_scripts that handles building scripts from functions.
"""

from distutils.command.build_scripts import build_scripts as old_build_scripts
from numpy.distutils import log
from numpy.distutils.misc_util import is_string

class build_scripts(old_build_scripts):

    def generate_scripts(self, scripts):
        new_scripts = []
        func_scripts = []
        for script in scripts:
            if is_string(script):
                new_scripts.append(script)
            else:
                func_scripts.append(script)
        if not func_scripts:
            return new_scripts

        build_dir = self.build_dir
        self.mkpath(build_dir)
        for func in func_scripts:
            script = func(build_dir)
            if not script:
                continue
            if is_string(script):
                log.info("  adding '%s' to scripts" % (script,))
                new_scripts.append(script)
            else:
                [log.info("  adding '%s' to scripts" % (s,)) for s in script]
                new_scripts.extend(list(script))
        return new_scripts

    def run (self):
        if not self.scripts:
            return

        self.scripts = self.generate_scripts(self.scripts)

        return old_build_scripts.run(self)

    def get_source_files(self):
        from numpy.distutils.misc_util import get_script_files
        return get_script_files(self.scripts)

import os
import sys
from distutils.command.bdist_rpm import bdist_rpm as old_bdist_rpm

class bdist_rpm(old_bdist_rpm):

    def _make_spec_file(self):
        spec_file = old_bdist_rpm._make_spec_file(self)

        # Replace hardcoded setup.py script name
        # with the real setup script name.
        setup_py = os.path.basename(sys.argv[0])
        if setup_py == 'setup.py':
            return spec_file
        new_spec_file = []
        for line in spec_file:
            line = line.replace('setup.py',setup_py)
            new_spec_file.append(line)
        return new_spec_file

""" Modified version of build_clib that handles fortran source files.
"""

from distutils.command.build_clib import build_clib as old_build_clib
from distutils.errors import DistutilsSetupError

from numpy.distutils import log
from distutils.dep_util import newer_group
from numpy.distutils.misc_util import filter_sources, has_f_sources,\
     has_cxx_sources, all_strings, get_lib_source_files, is_sequence

class build_clib(old_build_clib):

    description = "build C/C++/F libraries used by Python extensions"

    user_options = old_build_clib.user_options + [
        ('fcompiler=', None,
         "specify the Fortran compiler type"),
        ]

    def initialize_options(self):
        old_build_clib.initialize_options(self)
        self.fcompiler = None
        return

    def finalize_options(self):
        old_build_clib.finalize_options(self)
        self.set_undefined_options('build_ext',
                                   ('fcompiler', 'fcompiler'))
        return

    def have_f_sources(self):
        for (lib_name, build_info) in self.libraries:
            if has_f_sources(build_info.get('sources',[])):
                return True
        return False

    def have_cxx_sources(self):
        for (lib_name, build_info) in self.libraries:
            if has_cxx_sources(build_info.get('sources',[])):
                return True
        return False

    def run(self):
        if not self.libraries:
            return

        # Make sure that library sources are complete.
        for (lib_name, build_info) in self.libraries:
            if not all_strings(build_info.get('sources',[])):
                self.run_command('build_src')

        from distutils.ccompiler import new_compiler
        self.compiler = new_compiler(compiler=self.compiler,
                                     dry_run=self.dry_run,
                                     force=self.force)
        self.compiler.customize(self.distribution,
                                need_cxx=self.have_cxx_sources())

        libraries = self.libraries
        self.libraries = None
        self.compiler.customize_cmd(self)
        self.libraries = libraries

        self.compiler.show_customization()

        if self.have_f_sources():
            from numpy.distutils.fcompiler import new_fcompiler
            self.fcompiler = new_fcompiler(compiler=self.fcompiler,
                                           verbose=self.verbose,
                                           dry_run=self.dry_run,
                                           force=self.force)
            self.fcompiler.customize(self.distribution)

            libraries = self.libraries
            self.libraries = None
            self.fcompiler.customize_cmd(self)
            self.libraries = libraries

            self.fcompiler.show_customization()

        self.build_libraries(self.libraries)
        return

    def get_source_files(self):
        self.check_library_list(self.libraries)
        filenames = []
        for lib in self.libraries:
            filenames.extend(get_lib_source_files(lib))
        return filenames

    def build_libraries(self, libraries):


        for (lib_name, build_info) in libraries:
            # default compilers
            compiler = self.compiler
            fcompiler = self.fcompiler

            sources = build_info.get('sources')
            if sources is None or not is_sequence(sources):
                raise DistutilsSetupError, \
                      ("in 'libraries' option (library '%s'), " +
                       "'sources' must be present and must be " +
                       "a list of source filenames") % lib_name
            sources = list(sources)


            
            lib_file = compiler.library_filename(lib_name,
                                                 output_dir=self.build_clib)

            depends = sources + build_info.get('depends',[])
            if not (self.force or newer_group(depends, lib_file, 'newer')):
                log.debug("skipping '%s' library (up-to-date)", lib_name)
                continue
            else:
                log.info("building '%s' library", lib_name)


            config_fc = build_info.get('config_fc',{})
            if fcompiler is not None and config_fc:
                log.info('using setup script specified config_fc '\
                         'for fortran compiler: %s' \
                         % (config_fc))
                from numpy.distutils.fcompiler import new_fcompiler
                fcompiler = new_fcompiler(compiler=self.fcompiler.compiler_type,
                                          verbose=self.verbose,
                                          dry_run=self.dry_run,
                                          force=self.force)
                fcompiler.customize(config_fc)

            macros = build_info.get('macros')
            include_dirs = build_info.get('include_dirs')
            extra_postargs = build_info.get('extra_compiler_args') or []

            c_sources, cxx_sources, f_sources, fmodule_sources \
                       = filter_sources(sources)

            if self.compiler.compiler_type=='msvc':
                # this hack works around the msvc compiler attributes
                # problem, msvc uses its own convention :(
                c_sources += cxx_sources
                cxx_sources = []

            if fmodule_sources:
                print 'XXX: Fortran 90 module support not implemented or tested'
                f_sources.extend(fmodule_sources)

            objects = []
            if c_sources:
                log.info("compiling C sources")
                objects = compiler.compile(c_sources,
                                           output_dir=self.build_temp,
                                           macros=macros,
                                           include_dirs=include_dirs,
                                           debug=self.debug,
                                           extra_postargs=extra_postargs)

            if cxx_sources:
                log.info("compiling C++ sources")
                old_compiler = self.compiler.compiler_so[0]
                self.compiler.compiler_so[0] = self.compiler.compiler_cxx[0]

                cxx_objects = compiler.compile(cxx_sources,
                                               output_dir=self.build_temp,
                                               macros=macros,
                                               include_dirs=include_dirs,
                                               debug=self.debug,
                                               extra_postargs=extra_postargs)
                objects.extend(cxx_objects)

                self.compiler.compiler_so[0] = old_compiler

            if f_sources:
                log.info("compiling Fortran sources")
                f_objects = fcompiler.compile(f_sources,
                                              output_dir=self.build_temp,
                                              macros=macros,
                                              include_dirs=include_dirs,
                                              debug=self.debug,
                                              extra_postargs=[])
                objects.extend(f_objects)

            self.compiler.create_static_lib(objects, lib_name,
                                            output_dir=self.build_clib,
                                            debug=self.debug)

            clib_libraries = build_info.get('libraries',[])
            for lname,binfo in libraries:
                if lname in clib_libraries:
                    clib_libraries.extend(binfo[1].get('libraries',[]))
            if clib_libraries:
                build_info['libraries'] = clib_libraries

        return

from setuptools.command.egg_info import egg_info as _egg_info

class egg_info(_egg_info):
    def run(self):
        self.run_command("build_src")
        _egg_info.run(self)

import sys
if 'setuptools' in sys.modules:
    import setuptools.command.install as old_install_mod
else:
    import distutils.command.install as old_install_mod
old_install = old_install_mod.install
from distutils.file_util import write_file

class install(old_install):

    def finalize_options (self):
        old_install.finalize_options(self)
        self.install_lib = self.install_libbase

    def run(self):
        r = old_install.run(self)
        if self.record:
            # bdist_rpm fails when INSTALLED_FILES contains
            # paths with spaces. Such paths must be enclosed
            # with double-quotes.
            f = open(self.record,'r')
            lines = []
            need_rewrite = False
            for l in f.readlines():
                l = l.rstrip()
                if ' ' in l:
                    need_rewrite = True
                    l = '"%s"' % (l)
                lines.append(l)
            f.close()
            if need_rewrite:
                self.execute(write_file,
                             (self.record, lines),
                             "re-writing list of installed files to '%s'" %
                             self.record)
        return r

from distutils.command.install_data import install_data as old_install_data

#data installer with improved intelligence over distutils
#data files are copied into the project directory instead
#of willy-nilly
class install_data (old_install_data):

    def finalize_options (self):
        self.set_undefined_options('install',
                                   ('install_lib', 'install_dir'),
                                   ('root', 'root'),
                                   ('force', 'force'),
                                  )

