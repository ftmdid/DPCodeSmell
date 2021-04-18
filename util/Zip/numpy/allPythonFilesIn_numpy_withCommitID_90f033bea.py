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
$Revision$
$Date$
Pearu Peterson
"""

__version__ = "$Id$"

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

    def _is_Itanium(self):
        return re.match(r'.*?Itanium\b',
                        self.info[0]['model name']) is not None



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

    def _has_3dnow(self):
        return re.match(r'.*?\b3dnow\b',self.info[0]['flags']) is not None

    def _has_3dnowext(self):
        return re.match(r'.*?\b3dnowext\b',self.info[0]['flags']) is not None

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

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

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
        opt = FCompiler.get_library_dirs(self)
        d = os.environ.get('LAHEY')
        if d:
            opt.append(os.path.join(d,'lib'))
        return opt
    def get_libraries(self):
        opt = FCompiler.get_libraries(self)
        opt.extend(['fj9f6', 'fj9i6', 'fj9ipp', 'fj9e6'])
        return opt

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='lahey')
    compiler.customize()
    print compiler.get_version()

import os,sys,string
import re
import types

if sys.version[:3]<='2.1':
    from distutils import util
    util_get_platform = util.get_platform
    util.get_platform = lambda : util_get_platform().replace(' ','_')

# Hooks for colored terminal output.
# See also http://www.livinglogic.de/Python/ansistyle
def terminal_has_colors():
    if not hasattr(sys.stdout,'isatty') or not sys.stdout.isatty(): 
        return 0
    try:
        import curses
        curses.setupterm()
        return (curses.tigetnum("colors") >= 0
                and curses.tigetnum("pairs") >= 0
                and ((curses.tigetstr("setf") is not None 
                      and curses.tigetstr("setb") is not None) 
                     or (curses.tigetstr("setaf") is not None
                         and curses.tigetstr("setab") is not None)
                     or curses.tigetstr("scp") is not None))
    except: pass
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

class PostponedException:
    """Postpone exception until an attempt is made to use a resource."""
    #Example usage:
    #  try: import foo
    #  except ImportError: foo = PostponedException()
    __all__ = []
    def __init__(self):
        self._info = sys.exc_info()[:2]
        self.__doc__ = '%s: %s' % tuple(self._info)
    def __getattr__(self,name):
        raise self._info[0],self._info[1]

def get_path(mod_name,parent_path=None):
    """ This function makes sure installation is done from the
        correct directory no matter if it is installed from the
        command line or from another package or run_setup function.
        
    """
    if mod_name == '__main__':
        d = os.path.abspath('.')
    elif mod_name == '__builtin__':
        #builtin if/then added by Pearu for use in core.run_setup.        
        d = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        mod = __import__(mod_name)
        file = mod.__file__
        d = os.path.dirname(os.path.abspath(file))
    if parent_path is not None:
        pd = os.path.abspath(parent_path)
        if pd==d[:len(pd)]:
            d = d[len(pd)+1:]
    return d
    
def add_local_to_path(mod_name):
    local_path = get_path(mod_name)
    sys.path.insert(0,local_path)

def add_grandparent_to_path(mod_name):
    local_path = get_path(mod_name)
    gp_dir = os.path.split(local_path)[0]
    sys.path.insert(0,gp_dir)

def restore_path():
    del sys.path[0]

def append_package_dir_to_path(package_name):           
    """ Search for a directory with package_name and append it to PYTHONPATH
        
        The local directory is searched first and then the parent directory.
    """
    # first see if it is in the current path
    # then try parent.  If it isn't found, fail silently
    # and let the import error occur.
    
    # not an easy way to clean up after this...
    import os,sys
    if os.path.exists(package_name):
        sys.path.append(package_name)
    elif os.path.exists(os.path.join('..',package_name)):
        sys.path.append(os.path.join('..',package_name))

def get_package_config(package_name):
    """ grab the configuration info from the setup_xxx.py file
        in a package directory.  The package directory is searched
        from the current directory, so setting the path to the
        setup.py file directory of the file calling this is usually
        needed to get search the path correct.
    """
    append_package_dir_to_path(package_name)
    mod = __import__('setup_'+package_name)
    config = mod.configuration()
    return config

def package_config(primary,dependencies=[]):
    """ Create a configuration dictionary ready for setup.py from
        a list of primary and dependent package names.  Each
        package listed must have a directory with the same name
        in the current or parent working directory.  Further, it
        should have a setup_xxx.py module within that directory that
        has a configuration() function in it. 
    """
    config = []
    config.extend([get_package_config(x) for x in primary])
    config.extend([get_package_config(x) for x in dependencies])        
    config_dict = merge_config_dicts(config)
    return config_dict
        
list_keys = ['packages', 'ext_modules', 'data_files',
             'include_dirs', 'libraries', 'fortran_libraries',
             'headers']
dict_keys = ['package_dir']

def default_config_dict(name = None, parent_name = None):
    """ Return a configuration dictionary for usage in
    configuration() function defined in file setup_<name>.py.
    """
    d={}
    for key in list_keys: d[key] = []
    for key in dict_keys: d[key] = {}

    full_name = dot_join(parent_name,name)

    if full_name:
        # XXX: The following assumes that default_config_dict is called
        #      only from setup_<name>.configuration().
        #      Todo: implement check for this assumption.
        frame = get_frame(1)
        caller_name = eval('__name__',frame.f_globals,frame.f_locals)
        local_path = get_path(caller_name)
        test_path = os.path.join(local_path,'tests')
        if 0 and name and parent_name is None:
            # Useful for local builds
            d['version'] = get_version(path=local_path)
        if os.path.exists(os.path.join(local_path,'__init__.py')):
            d['packages'].append(full_name)
            d['package_dir'][full_name] = local_path
        if os.path.exists(test_path):
            d['packages'].append(dot_join(full_name,'tests'))
            d['package_dir'][dot_join(full_name,'tests')] = test_path
        d['name'] = full_name
        if 0 and not parent_name:
            # Include scipy_distutils to local distributions
            for p in ['.','..']:
                dir_name = os.path.abspath(os.path.join(local_path,
                                                        p,'scipy_distutils'))
                if os.path.exists(dir_name):
                    d['packages'].append('scipy_distutils')
                    d['packages'].append('scipy_distutils.command')
                    d['package_dir']['scipy_distutils'] = dir_name
                    break
    return d

def get_frame(level=0):
    try:
        return sys._getframe(level+1)
    except AttributeError:
        frame = sys.exc_info()[2].tb_frame
        for i in range(level+1):
            frame = frame.f_back
        return frame

def merge_config_dicts(config_list):
    result = default_config_dict()
    for d in config_list:
        name = d.get('name',None)
        if name is not None:
            result['name'] = name
            break
    for d in config_list:
        for key in list_keys:
            result[key].extend(d.get(key,[]))
        for key in dict_keys:
            result[key].update(d.get(key,{}))
    return result

def dict_append(d,**kws):
    for k,v in kws.items():
        if d.has_key(k):
            d[k].extend(v)
        else:
            d[k] = v

def dot_join(*args):
    return string.join(filter(None,args),'.')

def fortran_library_item(lib_name,
                         sources,
                         **attrs
                         ):   #obsolete feature
    """ Helper function for creating fortran_libraries items. """
    build_info = {'sources':sources}
    known_attrs = ['module_files','module_dirs',
                   'libraries','library_dirs']
    for key,value in attrs.items():
        if key not in known_attrs:
            raise TypeError,\
                  "fortran_library_item() got an unexpected keyword "\
                  "argument '%s'" % key
        build_info[key] = value
    
    return (lib_name,build_info)

def get_environ_include_dirs():  #obsolete feature
    includes = []
    if os.environ.has_key('PYTHONINCLUDE'):
        includes = os.environ['PYTHONINCLUDE'].split(os.pathsep)
    return includes

def get_build_temp():
    from distutils.util import get_platform
    plat_specifier = ".%s-%s" % (get_platform(), sys.version[0:3])
    return os.path.join('build','temp'+plat_specifier)

class SourceGenerator:  #obsolete feature
    """ SourceGenerator
    func    - creates target, arguments are (target,sources)+args
    sources - target source files
    args    - extra arguments to func

    If func is None then target must exist and it is touched whenever
    sources are newer.
    """
    def __init__(self,func,target,sources=[],*args):
        if not os.path.isabs(target) and func is not None:
            g = sys._getframe(1).f_globals
            fn = g.get('__file__',g.get('__name__'))
            if fn=='__main__': fn = sys.argv[0]
            caller_dir = os.path.abspath(os.path.dirname(fn))
            prefix = os.path.commonprefix([caller_dir,os.getcwd()])
            target_dir = caller_dir[len(prefix)+1:]
            target = os.path.join(get_build_temp(),target_dir,target)
        self.func = func
        self.target = target
        self.sources = sources
        self.args = args
    def __str__(self):
        return str(self.target)
    def generate(self):
        from distutils import dep_util,dir_util
        if dep_util.newer_group(self.sources,self.target):
            print 'Running generate',self.target
            dir_util.mkpath(os.path.dirname(self.target),verbose=1)
            if self.func is None:
                # Touch target
                os.utime(self.target,None)
            else:
                self.func(self.target,self.sources,*self.args)
        assert os.path.exists(self.target),`self.target`
        return self.target
    def __call__(self, extension, src_dir):
        return self.generate()

class SourceFilter:  #obsolete feature
    """ SourceFilter
    func    - implements criteria to filter sources
    sources - source files
    args    - extra arguments to func
    """
    def __init__(self,func,sources,*args):
        self.func = func
        self.sources = sources
        self.args = args
    def filter(self):
        return self.func(self.sources,*self.args)
    def __call__(self, extension, src_dir):
        return self.filter()

##

#XXX need support for .C that is also C++
cxx_ext_match = re.compile(r'.*[.](cpp|cxx|cc)\Z',re.I).match
fortran_ext_match = re.compile(r'.*[.](f90|f95|f77|for|ftn|f)\Z',re.I).match
f90_ext_match = re.compile(r'.*[.](f90|f95)\Z',re.I).match
f90_module_name_match = re.compile(r'\s*module\s*(?P<name>[\w_]+)',re.I).match
def get_f90_modules(source):
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

def has_f_sources(sources):
    """ Return True if sources contains Fortran files """
    for source in sources:
        if fortran_ext_match(source):
            return 1
    return 0

def has_cxx_sources(sources):
    """ Return True if sources contains C++ files """
    for source in sources:
        if cxx_ext_match(source):
            return 1
    return 0

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
            modules = get_f90_modules(source)
            if modules:
                fmodule_sources.append(source)
            else:
                f_sources.append(source)
        elif cxx_ext_match(source):
            cxx_sources.append(source)
        else:
            c_sources.append(source)            
    return c_sources, cxx_sources, f_sources, fmodule_sources

import os
import sys

from cpuinfo import cpu
from gnufcompiler import GnuFCompiler
#from fcompiler import FCompiler

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
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='vast')
    compiler.customize()
    print compiler.get_version()

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

class NAGFCompiler(FCompiler):

    compiler_type = 'nag'
    version_pattern =  r'NAGWare Fortran 95 compiler Release (?P<version>[^\s]*)'

    executables = {
        'version_cmd'  : ["f95", "-V"],
        'compiler_f77' : ["f95", "-fixed"],
        'compiler_fix' : ["f95", "-fixed"],
        'compiler_f90' : ["f95"],
        'linker_so'    : ["f95","-Wl,shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    def get_flags_opt(self):
        return ['-O4']
    def get_flags_arch(self):
        return ['-target=native']
    def get_flags_debug(self):
        return ['-g','-gline','-g90','-nan','-C']

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='nag')
    compiler.customize()
    print compiler.get_version()

"""scipy_distutils.fcompiler

Contains FCompiler, an abstract base class that defines the interface
for the Scipy_istutils Fortran compiler abstraction model.

"""

import re
import os
import sys
import atexit
from types import StringType, NoneType, ListType, TupleType
from glob import glob

from distutils.version import StrictVersion
from distutils.ccompiler import CCompiler, gen_lib_options
# distutils.ccompiler provides the following functions:
#   gen_preprocess_options(macros, include_dirs)
#   gen_lib_options(compiler, library_dirs, runtime_library_dirs, libraries)
from distutils.errors import DistutilsModuleError,DistutilsArgError,\
     DistutilsExecError,CompileError,LinkError,DistutilsPlatformError
from distutils.core import Command
from distutils.util import split_quoted
from distutils.fancy_getopt import FancyGetopt
from distutils.version import LooseVersion
from distutils.sysconfig import get_config_var

from scipy_distutils.command.config_compiler import config_fc

import log
from exec_command import find_executable, exec_command


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
    # CCompiler defines the following attributes:
    #   compiler_type
    #   src_extensions
    #   obj_extension
    #   static_lib_extension
    #   shared_lib_extension
    #   static_lib_format
    #   shared_lib_format
    #   exe_extension
    #   language_map    ### REDEFINED
    #   language_order  ### REDEFINED
    # and the following public methods:
    #   set_executables(**args)
    #     set_executable(key,value)
    #   define_macro(name, value=None)
    #   undefine_macro(name)
    #   add_include_dir(dir)
    #   set_include_dirs(dirs)
    #   add_library(libname)
    #   set_libraries(libnames)
    #   add_library_dir(dir)
    #   set_library_dirs(dirs)
    #   add_runtime_library_dir(dir)
    #   set_runtime_library_dirs(dirs)
    #   add_link_object(object)
    #   set_link_objects(objects)
    #
    #   detect_language(sources)  ### USABLE
    #
    #   preprocess(source,output_file=None,macros=None,include_dirs=None,
    #              extra_preargs=None,extra_postargs=None)
    #   compile(sources, output_dir=None, macros=None,
    #           include_dirs=None, debug=0, extra_preargs=None,
    #           extra_postargs=None, depends=None)
    #   create_static_lib(objects,output_libname,output_dir=None,debug=0,target_lang=None):
    #   link(target_desc, objects, output_filename, output_dir=None,
    #        libraries=None, library_dirs=None, runtime_library_dirs=None,
    #        export_symbols=None, debug=0, extra_preargs=None, extra_postargs=None,
    #        build_temp=None, target_lang=None)
    #   link_shared_lib(objects, output_libname, output_dir=None,
    #                   libraries=None, library_dirs=None, runtime_library_dirs=None,
    #                   export_symbols=None, debug=0, extra_preargs=None,
    #                   extra_postargs=None, build_temp=None, target_lang=None)
    #   link_shared_object(objects,output_filename,output_dir=None,
    #                      libraries=None,library_dirs=None,runtime_library_dirs=None,
    #                      export_symbols=None,debug=0,extra_preargs=None,
    #                      extra_postargs=None,build_temp=None,target_lang=None)
    #   link_executable(objects,output_progname,output_dir=None,
    #                   libraries=None,library_dirs=None,runtime_library_dirs=None,
    #                   debug=0,extra_preargs=None,extra_postargs=None,target_lang=None)
    #
    #   library_dir_option(dir)
    #   runtime_library_dir_option(dir)
    #   library_option(lib)
    #   has_function(funcname,includes=None,include_dirs=None,
    #                libraries=None,library_dirs=None)
    #   find_library_file(dirs, lib, debug=0)
    #
    #   object_filenames(source_filenames, strip_dir=0, output_dir='')
    #   shared_object_filename(basename, strip_dir=0, output_dir='')
    #   executable_filenamee(basename, strip_dir=0, output_dir='')
    #   library_filename(libname, lib_type='static',strip_dir=0, output_dir=''):
    #
    #   announce(msg, level=1)
    #   debug_print(msg)
    #   warn(msg)
    #   execute(func, args, msg=None, level=1)
    #   spawn(cmd)
    #   move_file(src,dst)
    #   mkpath(name, mode=0777)
    #

    language_map = {'.f':'f77',
                    '.for':'f77',
                    '.ftn':'f77',
                    '.f77':'f77',
                    '.f90':'f90',
                    '.f95':'f90'}
    language_order = ['f90','f77']

    version_pattern = None

    executables = {
        'version_cmd'  : ["f77","-v"],
        'compiler_f77' : ["f77"],
        'compiler_f90' : ["f90"],
        'compiler_fix' : ["f90","-fixed"],
        'linker_so'    : ["f90","-shared"],
        #'linker_exe'   : ["f90"],  #  XXX do we need it??
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

    src_extensions = ['.for','.ftn','.f77','.f','.f90','.f95']
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

    def get_version(self, force=0, ok_status=[0]):
        """ Compiler version. Returns None if compiler is not available. """
        if not force and hasattr(self,'version'):
            return self.version

        cmd = ' '.join(self.version_cmd)
        status, output = self.exec_command(cmd,use_tee=0)
        version = None
        if status in ok_status:
            m = re.match(self.version_pattern,output)
            if m:
                version = m.group('version')
                assert version,`version`
                version = LooseVersion(version)
        self.version = version
        return version

    ############################################################

    ## Public methods:

    def customize(self, dist=None):
        """ Customize Fortran compiler.

        This method gets Fortran compiler specific information from
        (i) class definition, (ii) environment, (iii) distutils config
        files, and (iv) command line.

        This method should be always called after constructing a
        compiler instance. But not in __init__ because Distribution
        instance is needed for (iii) and (iv).
        """
        if dist is None:
            # These hooks are for testing only!
            from dist import Distribution
            dist = Distribution()
            dist.script_name = os.path.basename(sys.argv[0])
            dist.script_args = ['config_fc'] + sys.argv[1:]
            dist.cmdclass['config_fc'] = config_fc
            dist.parse_config_files()
            dist.parse_command_line()

        conf = dist.get_option_dict('config_fc')

        noopt = conf.get('noopt',[None,0])[1]
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
            self.set_executables(compiler_f90=[f90]+f90flags+fflags)
        if fix:
            self.set_executables(compiler_fix=[fix]+fixflags+fflags)

        #XXX: Do we need LDSHARED->SOSHARED, LDFLAGS->SOFLAGS
        linker_so = self.__get_cmd(self.get_linker_so,'LDSHARED')
        if linker_so:
            linker_so_flags = self.__get_flags(self.get_flags_linker_so,'LDFLAGS')
            self.set_executables(linker_so=[linker_so]+linker_so_flags)

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

    def customize_cmd(self, cmd):
        if cmd.include_dirs is not None:
            self.set_include_dirs(cmd.include_dirs)
        if cmd.define is not None:
            for (name,value) in cmd.define:
                self.define_macro(name, value)
        if cmd.undef is not None:
            for macro in cmd.undef:
                self.undefine_macro(macro)
        if cmd.libraries is not None:
            self.set_libraries(self.get_libraries() + cmd.libraries)
        if cmd.library_dirs is not None:
            self.set_library_dirs(self.get_library_dirs() + cmd.library_dirs)
        if cmd.rpath is not None:
            self.set_runtime_library_dirs(cmd.rpath)
        if cmd.link_objects is not None:
            self.set_link_objects(cmd.link_objects)
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

    def exec_command(self,*args,**kws):
        """ Return status,output of a command. """
        quiet = kws.get('quiet',1)
        try: del kws['quiet']
        except KeyError: pass
        if not quiet:
            log.info('%s.exec_command(*%s,**%s)' % (self.__class__.__name__,
                                                    args,kws))
        status, output = exec_command(*args,**kws)
        if not quiet:
            log.info('*****status:%s\n*****output:\n%s\n*****' % (status,output))
        return status, output

    ###################

    def _get_cc_args(self, pp_opts, debug, before):
        #XXX
        print self.__class__.__name__ + '._get_cc_args:',pp_opts, debug, before
        return []

    def _compile(self, obj, src, ext, cc_args, extra_postargs, pp_opts):
        """Compile 'src' to product 'obj'."""
        print self.__class__.__name__ + '._compile:',obj, src, ext, cc_args, extra_postargs, pp_opts

        if is_f_file(src):
            compiler = self.compiler_f77
        elif is_free_format(src):
            compiler = self.compiler_f90
            if compiler is None:
                raise DistutilsExecError, 'f90 not supported by '\
                      +self.__class__.__name__
        else:
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

        command = compiler + cc_args + pp_opts + s_args + o_args + extra_postargs
        log.info(' '.join(command))
        try:
            s,o = self.exec_command(command)
        except DistutilsExecError, msg:
            raise CompileError, msg
        if s:
            raise CompileError, o

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

    if sys.version[:3]<'2.3':
        def compile(self, sources, output_dir=None, macros=None,
                    include_dirs=None, debug=0, extra_preargs=None,
                    extra_postargs=None, depends=None):
            if output_dir is None: output_dir = self.output_dir
            if macros is None: macros = self.macros
            elif type(macros) is ListType: macros = macros + (self.macros or [])
            if include_dirs is None: include_dirs = self.include_dirs
            elif type(include_dirs) in (ListType, TupleType):
                include_dirs = list(include_dirs) + (self.include_dirs or [])
            if extra_preargs is None: extra_preargs=[]
            from distutils.sysconfig import python_build
            objects = self.object_filenames(sources,strip_dir=python_build,
                                            output_dir=output_dir)
            from distutils.ccompiler import gen_preprocess_options
            pp_opts = gen_preprocess_options(macros, include_dirs)
            build = {}
            for i in range(len(sources)):
                src,obj = sources[i],objects[i]
                ext = os.path.splitext(src)[1]
                self.mkpath(os.path.dirname(obj))
                build[obj] = src, ext
            cc_args = self._get_cc_args(pp_opts, debug, extra_preargs)
            for obj, (src, ext) in build.items():
                self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)
            return objects
        def detect_language(self, sources):
            return

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
        if type(output_dir) not in (StringType, NoneType):
            raise TypeError, "'output_dir' must be a string or None"
        if output_dir is not None:
            output_filename = os.path.join(output_dir, output_filename)

        if self._need_link(objects, output_filename):
            if self.library_switch[-1]==' ':
                o_args = [self.library_switch.strip(),output_filename]
            else:
                o_args = [self.library_switch.strip()+output_filename]
            ld_args = (objects + self.objects +
                       lib_opts + o_args)
            #if debug:
            #    ld_args[:0] = ['-g']
            if extra_preargs:
                ld_args[:0] = extra_preargs
            if extra_postargs:
                ld_args.extend(extra_postargs)
            self.mkpath(os.path.dirname(output_filename))
            if target_desc == CCompiler.EXECUTABLE:
                raise NotImplementedError,self.__class__.__name__+'.linker_exe attribute'
            else:
                linker = self.linker_so[:]
            command = linker + ld_args
            log.info(' '.join(command))
            try:
                s,o = self.exec_command(command)
            except DistutilsExecError, msg:
                raise LinkError, msg
            if s:
                raise LinkError, o
        else:
            log.debug("skipping %s (up-to-date)", output_filename)
        return

    ############################################################

    ## Private methods:

    def __get_cmd(self, command, envvar=None, confvar=None):
        if command is None:
            var = None
        elif type(command) is type(''):
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
        elif type(command) is type(''):
            var = self.executables[command][1:]
        else:
            var = command()
        if envvar is not None:
            var = os.environ.get(envvar, var)
        if confvar is not None:
            var = confvar[0].get(confvar[1], [None,var])[1]
        if type(var) is type(''):
            var = split_quoted(var)
        return var

    ## class FCompiler

##############################################################################

fcompiler_class = {'gnu':('gnufcompiler','GnuFCompiler',
                          "GNU Fortran Compiler"),
                   'pg':('pgfcompiler','PGroupFCompiler',
                         "Portland Group Fortran Compiler"),
                   'absoft':('absoftfcompiler','AbsoftFCompiler',
                             "Absoft Corp Fortran Compiler"),
                   'mips':('mipsfcompiler','MipsFCompiler',
                           "MIPSpro Fortran Compiler"),
                   'sun':('sunfcompiler','SunFCompiler',
                          "Sun|Forte Fortran 95 Compiler"),
                   'intel':('intelfcompiler','IntelFCompiler',
                            "Intel Fortran Compiler for 32-bit apps"),
                   'intelv':('intelfcompiler','IntelVisualFCompiler',
                             "Intel Visual Fortran Compiler for 32-bit apps"),
                   'intele':('intelfcompiler','IntelItaniumFCompiler',
                             "Intel Fortran Compiler for Itanium apps"),
                   'intelev':('intelfcompiler','IntelItaniumVisualFCompiler',
                              "Intel Visual Fortran Compiler for Itanium apps"),
                   'nag':('nagfcompiler','NAGFCompiler',
                          "NAGWare Fortran 95 Compiler"),
                   'compaq':('compaqfcompiler','CompaqFCompiler',
                             "Compaq Fortran Compiler"),
                   'compaqv':('compaqfcompiler','CompaqVisualFCompiler',
                             "DIGITAL|Compaq Visual Fortran Compiler"),
                   'vast':('vastfcompiler','VastFCompiler',
                           "Pacific-Sierra Research Fortran 90 Compiler"),
                   'hpux':('hpuxfcompiler','HPUXFCompiler',
                           "HP Fortran 90 Compiler"),
                   'lahey':('laheyfcompiler','LaheyFCompiler',
                            "Lahey/Fujitsu Fortran 95 Compiler"),
                   'f':('fcompiler','FFCompiler',
                        "Fortran Company/NAG F Compiler"),
                   }

_default_compilers = (
    # Platform mappings
    ('win32',('gnu','intelv','absoft','compaqv','intelitanium')),
    ('cygwin.*',('gnu','intelv','absoft','compaqv','intelitanium')),
    ('linux.*',('gnu','intel','lahey','pg','absoft','nag','vast','compaq',
                'intelitanium')),
    ('sunos.*',('forte','gnu','sun')),
    ('irix',('mips','gnu')),
    # OS mappings
    ('posix',('gnu',)),
    ('nt',('gnu',)),
    ('mac',('gnu',)),
    )

def get_default_fcompiler(osname=None, platform=None):
    """ Determine the default Fortran compiler to use for the given platform. """
    if osname is None:
        osname = os.name
    if platform is None:
        platform = sys.platform
    for pattern, compiler in _default_compilers:
        if re.match(pattern, platform) is not None or \
               re.match(pattern, osname) is not None:
            if type(compiler) is type(()):
                return compiler[0]
            return compiler
    return 'gnu'

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
        module_name = 'scipy_distutils.'+module_name
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

    return klass(None, dry_run, force)


def show_fcompilers(dist = None):
    """ Print list of available compilers (used by the "--help-fcompiler"
    option to "config_fc").
    """
    if dist is None:
        from dist import Distribution
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
        except:
            print sys.exc_info()[0],sys.exc_info()[1]
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
_free_f90_start = re.compile(r'[^c*][^\s\d\t]',re.I).match
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
            if _free_f90_start(line[:5]) or line[-2:-1]=='&':
                result = 1
                break
        line = f.readline()
    f.close()
    return result

if __name__ == '__main__':
    show_fcompilers()

# Python 2.3 distutils.log backported to Python 2.1.x, 2.2.x

import sys

if sys.version[:3]>='2.3':
    from distutils.log import *
    from distutils.log import Log as old_Log
    from distutils.log import _global_log
    class Log(old_Log):
        def _log(self, level, msg, args):
            if level>= self.threshold:
                print _global_color_map[level](msg % args)
                sys.stdout.flush()
    _global_log.__class__ = Log

else:
    exec """
# Here follows (slightly) modified copy of Python 2.3 distutils/log.py

DEBUG = 1
INFO = 2
WARN = 3
ERROR = 4
FATAL = 5
class Log:

    def __init__(self, threshold=WARN):
        self.threshold = threshold

    def _log(self, level, msg, args):
        if level >= self.threshold:
            print _global_color_map[level](msg % args)
            sys.stdout.flush()

    def log(self, level, msg, *args):
        self._log(level, msg, args)

    def debug(self, msg, *args):
        self._log(DEBUG, msg, args)
    
    def info(self, msg, *args):
        self._log(INFO, msg, args)
    
    def warn(self, msg, *args):
        self._log(WARN, red_text(msg), args)
    
    def error(self, msg, *args):
        self._log(ERROR, msg, args)
    
    def fatal(self, msg, *args):
        self._log(FATAL, msg, args)

_global_log = Log()
log = _global_log.log
debug = _global_log.debug
info = _global_log.info
warn = _global_log.warn
error = _global_log.error
fatal = _global_log.fatal

def set_threshold(level):
    _global_log.threshold = level

def set_verbosity(v):
    if v <= 0:
        set_threshold(WARN)
    elif v == 1:
        set_threshold(INFO)
    elif v >= 2:
        set_threshold(DEBUG)
"""

from misc_util import red_text, yellow_text, cyan_text
_global_color_map = {
    DEBUG:cyan_text,
    INFO:yellow_text,
    WARN:red_text,
    ERROR:red_text,
    FATAL:red_text
}

set_verbosity(2)

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
    else:
        print file, 'ok'    

def dos2unix_one_dir(args,dir_name,file_names):
    for file in file_names:
        full_path = os.path.join(dir_name,file)
        dos2unix(full_path)
    
def dos2unix_dir(dir_name):
    os.path.walk(dir_name,dos2unix_one_dir,[])

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
    else:
        print file, 'ok'    

def unix2dos_one_dir(args,dir_name,file_names):
    for file in file_names:
        full_path = os.path.join(dir_name,file)
        unix2dos(full_path)
    
def unix2dos_dir(dir_name):
    os.path.walk(dir_name,unix2dos_one_dir,[])
        
if __name__ == "__main__":
    import sys
    dos2unix_dir(sys.argv[1])

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

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
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='mips')
    compiler.customize()
    print compiler.get_version()


# http://www.absoft.com/literature/osxuserguide.pdf
# http://www.absoft.com/documentation.html

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler, dummy_fortran_file

class AbsoftFCompiler(FCompiler):

    compiler_type = 'absoft'
    version_pattern = r'FORTRAN 77 Compiler (?P<version>[^\s*,]*).*?Absoft Corp'

    executables = {
        'version_cmd'  : ["f77", "-V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':dummy_fortran_file()}],
        'compiler_f77' : ["f77"],
        'compiler_fix' : ["f90"],
        'compiler_f90' : ["f90"],
        'linker_so'    : ["f77","-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    if os.name != 'nt':
        pic_flags = ['-fpic']
    module_dir_switch = None
    module_include_switch = '-p '

    def get_library_dirs(self):
        opt = FCompiler.get_library_dirs(self)
        d = os.environ.get('ABSOFT')
        if d:
            opt.append(d)
        return opt

    def get_libraries(self):
        opt = FCompiler.get_libraries(self)
        opt.extend(['fio','f77math','f90math'])
        if os.name =='nt':
            opt.append('COMDLG32')
        return opt

    def get_flags(self):
        opt = FCompiler.get_flags(self)
        if os.name != 'nt':
            opt.extend(['-s'])
        return opt

    def get_flags_f77(self):
        opt = FCompiler.get_flags_f77(self)
        opt.extend(['-N22','-N90','-N110'])
        if os.name != 'nt':
            opt.append('-f')
            if self.get_version():
                if self.get_version()<='4.6':
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
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='absoft')
    compiler.customize()
    print compiler.get_version()

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

DEF_HEADER = """LIBRARY		python%s.dll
;CODE		PRELOAD MOVEABLE DISCARDABLE
;DATA		PRELOAD SINGLE

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

#!/usr/bin/env python
"""
This file defines a set of system_info classes for getting
information about various resources (libraries, library directories,
include directories, etc.) in the system. Currently, the following
classes are available:
  atlas_info
  atlas_threads_info
  lapack_atlas_info
  blas_info
  lapack_info
  fftw_info,dfftw_info,sfftw_info
  fftw_threads_info,dfftw_threads_info,sfftw_threads_info
  djbfft_info
  x11_info
  lapack_src_info
  blas_src_info
  numpy_info
  numarray_info

Usage:
    info_dict = get_info(<name>)
  where <name> is a string 'atlas','x11','fftw','lapack','blas',
  'lapack_src', or 'blas_src'.

  Returned info_dict is a dictionary which is compatible with
  distutils.setup keyword arguments. If info_dict == {}, then the
  asked resource is not available (system_info could not find it).

Global parameters:
  system_info.search_static_first - search static libraries (.a)
             in precedence to shared ones (.so, .sl) if enabled.
  system_info.verbosity - output the results to stdout if enabled.

The file 'site.cfg' in the same directory as this module is read
for configuration options. The format is that used by ConfigParser (i.e.,
Windows .INI style). The section DEFAULT has options that are the default
for each section. The available sections are fftw, atlas, and x11. Appropiate
defaults are used if nothing is specified.

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

__revision__ = '$Id$'

import sys,os,re,types
import warnings
from distutils.errors import DistutilsError
from glob import glob
import ConfigParser

from distutils.sysconfig import get_config_vars

if sys.platform == 'win32':
    default_lib_dirs = ['C:\\'] # probably not very helpful...
    default_include_dirs = []
    default_src_dirs = []
    default_x11_lib_dirs = []
    default_x11_include_dirs = []
else:
    default_lib_dirs = ['/usr/local/lib', '/opt/lib', '/usr/lib']
    default_include_dirs = ['/usr/local/include',
                            '/opt/include', '/usr/include']
    default_src_dirs = ['/usr/local/src', '/opt/src']
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

so_ext = get_config_vars('SO')[0] or ''

def get_info(name):
    cl = {'atlas':atlas_info,
          'atlas_threads':atlas_threads_info,
          'lapack_atlas_threads':lapack_atlas_threads_info,
          'lapack_atlas':lapack_atlas_info,
          'x11':x11_info,
          'fftw':fftw_info,
          'dfftw':dfftw_info,
          'sfftw':sfftw_info,
          'fftw_threads':fftw_threads_info,
          'dfftw_threads':dfftw_threads_info,
          'sfftw_threads':sfftw_threads_info,
          'djbfft':djbfft_info,
          'blas':blas_info,
          'lapack':lapack_info,
          'lapack_src':lapack_src_info,
          'blas_src':blas_src_info,
          'numpy':numpy_info,
          'numarray':numarray_info,
          }.get(name.lower(),system_info)
    return cl().get_info()

class NotFoundError(DistutilsError):
    """Some third-party program or library is not found."""

class AtlasNotFoundError(NotFoundError):
    """
    Atlas (http://math-atlas.sourceforge.net/) libraries not found.
    Directories to search for the libraries can be specified in the
    scipy_distutils/site.cfg file (section [atlas]) or by setting
    the ATLAS environment variable."""

class LapackNotFoundError(NotFoundError):
    """
    Lapack (http://www.netlib.org/lapack/) libraries not found.
    Directories to search for the libraries can be specified in the
    scipy_distutils/site.cfg file (section [lapack]) or by setting
    the LAPACK environment variable."""

class LapackSrcNotFoundError(LapackNotFoundError):
    """
    Lapack (http://www.netlib.org/lapack/) sources not found.
    Directories to search for the sources can be specified in the
    scipy_distutils/site.cfg file (section [lapack_src]) or by setting
    the LAPACK_SRC environment variable."""

class BlasNotFoundError(NotFoundError):
    """
    Blas (http://www.netlib.org/blas/) libraries not found.
    Directories to search for the libraries can be specified in the
    scipy_distutils/site.cfg file (section [blas]) or by setting
    the BLAS environment variable."""

class BlasSrcNotFoundError(BlasNotFoundError):
    """
    Blas (http://www.netlib.org/blas/) sources not found.
    Directories to search for the sources can be specified in the
    scipy_distutils/site.cfg file (section [blas_src]) or by setting
    the BLAS_SRC environment variable."""

class FFTWNotFoundError(NotFoundError):
    """
    FFTW (http://www.fftw.org/) libraries not found.
    Directories to search for the libraries can be specified in the
    scipy_distutils/site.cfg file (section [fftw]) or by setting
    the FFTW environment variable."""

class DJBFFTNotFoundError(NotFoundError):
    """
    DJBFFT (http://cr.yp.to/djbfft.html) libraries not found.
    Directories to search for the libraries can be specified in the
    scipy_distutils/site.cfg file (section [djbfft]) or by setting
    the DJBFFT environment variable."""

class F2pyNotFoundError(NotFoundError):
    """
    f2py2e (http://cens.ioc.ee/projects/f2py2e/) module not found.
    Get it from above location, install it, and retry setup.py."""

class NumericNotFoundError(NotFoundError):
    """
    Numeric (http://www.numpy.org/) module not found.
    Get it from above location, install it, and retry setup.py."""

class X11NotFoundError(NotFoundError):
    """X11 libraries not found."""

class system_info:

    """ get_info() is the only public method. Don't use others.
    """
    section = 'DEFAULT'
    dir_env_var = None
    search_static_first = 0 # XXX: disabled by default, may disappear in
                            # future unless it is proved to be useful.
    verbosity = 1
    saved_results = {}

    def __init__ (self,
                  default_lib_dirs=default_lib_dirs,
                  default_include_dirs=default_include_dirs,
                  verbosity = 1,
                  ):
        self.__class__.info = {}
        self.local_prefixes = []
        defaults = {}
        defaults['library_dirs'] = os.pathsep.join(default_lib_dirs)
        defaults['include_dirs'] = os.pathsep.join(default_include_dirs)
        defaults['src_dirs'] = os.pathsep.join(default_src_dirs)
        defaults['search_static_first'] = str(self.search_static_first)
        self.cp = ConfigParser.ConfigParser(defaults)
        try:
            __file__
        except NameError:
            __file__ = sys.argv[0]
        cf = os.path.join(os.path.split(os.path.abspath(__file__))[0],
                          'site.cfg')
        self.cp.read([cf])
        if not self.cp.has_section(self.section):
            self.cp.add_section(self.section)
        self.search_static_first = self.cp.getboolean(self.section,
                                                      'search_static_first')
        assert isinstance(self.search_static_first, type(0))

    def set_info(self,**info):
        self.saved_results[self.__class__.__name__] = info

    def has_info(self):
        return self.saved_results.has_key(self.__class__.__name__)

    def get_info(self):
        """ Return a dictonary with items that are compatible
            with scipy_distutils.setup keyword arguments.
        """
        flag = 0
        if not self.has_info():
            flag = 1
            if self.verbosity>0:
                print self.__class__.__name__ + ':'
            if hasattr(self, 'calc_info'):
                self.calc_info()
            if self.verbosity>0:
                if not self.has_info():
                    print '  NOT AVAILABLE'
                    self.set_info()
                else:
                    print '  FOUND:'
        res = self.saved_results.get(self.__class__.__name__)
        if self.verbosity>0 and flag:
            for k,v in res.items():
                v = str(v)
                if k=='sources' and len(v)>200: v = v[:60]+' ...\n... '+v[-60:]
                print '    %s = %s'%(k,v)
            print
        return res

    def get_paths(self, section, key):
        dirs = self.cp.get(section, key).split(os.pathsep)
        if os.environ.has_key(self.dir_env_var):
            dirs = os.environ[self.dir_env_var].split(os.pathsep) + dirs
        default_dirs = self.cp.get('DEFAULT', key).split(os.pathsep)
        dirs.extend(default_dirs)
        ret = []
        [ret.append(d) for d in dirs if os.path.isdir(d) and d not in ret]
        if self.verbosity>1:
            print '(',key,'=',':'.join(ret),')'
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
            return default
        return [a.strip() for a in libs.split(',')]

    def check_libs(self,lib_dir,libs,opt_libs =[]):
        """ If static or shared libraries are available then return
            their info dictionary. """
        if self.search_static_first:
            exts = ['.a',so_ext]
        else:
            exts = [so_ext,'.a']
        for ext in exts:
            info = self._check_libs(lib_dir,libs,opt_libs,ext)
            if info is not None: return info

    def _lib_list(self, lib_dir, libs, ext):
        assert type(lib_dir) is type('')
        liblist = []
        for l in libs:
            p = self.combine_paths(lib_dir, 'lib'+l+ext)
            if p:
                assert len(p)==1
                liblist.append(p[0])
        return liblist

    def _extract_lib_names(self,libs):
        return [os.path.splitext(os.path.basename(p))[0][3:] \
                for p in libs]

    def _check_libs(self,lib_dir,libs, opt_libs, ext):
        found_libs = self._lib_list(lib_dir, libs, ext)
        if len(found_libs) == len(libs):
            found_libs = self._extract_lib_names(found_libs)
            info = {'libraries' : found_libs, 'library_dirs' : [lib_dir]}
            opt_found_libs = self._lib_list(lib_dir, opt_libs, ext)
            if len(opt_found_libs) == len(opt_libs):
                opt_found_libs = self._extract_lib_names(opt_found_libs)
                info['libraries'].extend(opt_found_libs)
            return info

    def combine_paths(self,*args):
        return combine_paths(*args,**{'verbosity':self.verbosity})

class fftw_info(system_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['rfftw', 'fftw']
    includes = ['fftw.h','rfftw.h']
    macros = [('SCIPY_FFTW_H',None)]

    def __init__(self):
        system_info.__init__(self)

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()
        incl_dirs = self.get_include_dirs()
        incl_dir = None
        libs = self.get_libs(self.section+'_libs', self.libs)
        info = None
        for d in lib_dirs:
            r = self.check_libs(d,libs)
            if r is not None:
                info = r
                break
        if info is not None:
            flag = 0
            for d in incl_dirs:
                if len(self.combine_paths(d,self.includes))==2:
                    dict_append(info,include_dirs=[d])
                    flag = 1
                    incl_dirs = [d]
                    incl_dir = d
                    break
            if flag:
                dict_append(info,define_macros=self.macros)
            else:
                info = None
        if info is not None:
            self.set_info(**info)

class dfftw_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['drfftw','dfftw']
    includes = ['dfftw.h','drfftw.h']
    macros = [('SCIPY_DFFTW_H',None)]

class sfftw_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['srfftw','sfftw']
    includes = ['sfftw.h','srfftw.h']
    macros = [('SCIPY_SFFTW_H',None)]

class fftw_threads_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['rfftw_threads','fftw_threads']
    includes = ['fftw_threads.h','rfftw_threads.h']
    macros = [('SCIPY_FFTW_THREADS_H',None)]

class dfftw_threads_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['drfftw_threads','dfftw_threads']
    includes = ['dfftw_threads.h','drfftw_threads.h']
    macros = [('SCIPY_DFFTW_THREADS_H',None)]

class sfftw_threads_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['srfftw_threads','sfftw_threads']
    includes = ['sfftw_threads.h','srfftw_threads.h']
    macros = [('SCIPY_SFFTW_THREADS_H',None)]

class djbfft_info(system_info):
    section = 'djbfft'
    dir_env_var = 'DJBFFT'

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
            p = self.combine_paths (d,['libdjbfft.a'])
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


class atlas_info(system_info):
    section = 'atlas'
    dir_env_var = 'ATLAS'
    _lib_names = ['f77blas','cblas']

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
                                   self._lib_names + ['atlas'])
        lapack_libs = self.get_libs('lapack_libs',['lapack'])
        atlas = None
        lapack = None
        atlas_1 = None
        for d in lib_dirs:
            atlas = self.check_libs(d,atlas_libs,[])
            lapack_atlas = self.check_libs(d,['lapack_atlas'],[])
            if atlas is not None:
                lib_dirs2 = self.combine_paths(d,['atlas*','ATLAS*'])+[d]
                for d2 in lib_dirs2:
                    lapack = self.check_libs(d2,lapack_libs,[])
                    if lapack is not None:
                        break
                else:
                    lapack = None
                if lapack is not None:
                    break
            if atlas:
                atlas_1 = atlas
        print self.__class__
        if atlas is None:
            atlas = atlas_1
        if atlas is None:
            return
        include_dirs = self.get_include_dirs()
        h = (self.combine_paths(lib_dirs+include_dirs,'cblas.h') or [None])[0]
        if h:
            h = os.path.dirname(h)
            dict_append(info,include_dirs=[h])

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
        for e in ['.a',so_ext]:
            fn = os.path.join(lapack_dir,'lib'+lapack_name+e)
            if os.path.exists(fn):
                lapack_lib = fn
                break
        if lapack_lib is not None:
            sz = os.stat(lapack_lib)[6]
            if sz <= 4000*1024:
                message = """
*********************************************************************
    Lapack library (from ATLAS) is probably incomplete:
      size of %s is %sk (expected >4000k)

    Follow the instructions in the KNOWN PROBLEMS section of the file
    scipy/INSTALL.txt.
*********************************************************************
""" % (lapack_lib,sz/1024)
                warnings.warn(message)
        self.set_info(**info)

class atlas_threads_info(atlas_info):
    _lib_names = ['ptf77blas','ptcblas']

class lapack_atlas_info(atlas_info):
    _lib_names = ['lapack_atlas'] + atlas_info._lib_names

class lapack_atlas_threads_info(atlas_threads_info):
    _lib_names = ['lapack_atlas'] + atlas_threads_info._lib_names

class lapack_info(system_info):
    section = 'lapack'
    dir_env_var = 'LAPACK'

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()

        lapack_libs = self.get_libs('lapack_libs', ['lapack'])
        for d in lib_dirs:
            lapack = self.check_libs(d,lapack_libs,[])
            if lapack is not None:
                info = lapack                
                break
        else:
            return
        self.set_info(**info)

class lapack_src_info(system_info):
    section = 'lapack_src'
    dir_env_var = 'LAPACK_SRC'

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
        info = {'sources':sources}
        self.set_info(**info)


class blas_info(system_info):
    section = 'blas'
    dir_env_var = 'BLAS'

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()

        blas_libs = self.get_libs('blas_libs', ['blas'])
        for d in lib_dirs:
            blas = self.check_libs(d,blas_libs,[])
            if blas is not None:
                info = blas                
                break
        else:
            return
        self.set_info(**info)

class blas_src_info(system_info):
    section = 'blas_src'
    dir_env_var = 'BLAS_SRC'

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
        info = {'sources':sources}
        self.set_info(**info)

class x11_info(system_info):
    section = 'x11'

    def __init__(self):
        system_info.__init__(self,
                             default_lib_dirs=default_x11_lib_dirs,
                             default_include_dirs=default_x11_include_dirs)

    def calc_info(self):
        if sys.platform  in ['win32','cygwin']:
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

class numpy_info(system_info):
    section = 'numpy'
    modulename = 'Numeric'

    def __init__(self):
        from distutils.sysconfig import get_python_inc
        py_incl_dir = get_python_inc()
        include_dirs = [py_incl_dir]
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
        macros = [(self.modulename.upper()+'_VERSION',
                   '"%s"' % (module.__version__))]
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

class numarray_info(numpy_info):
    section = 'numarray'
    modulename = 'numarray'

## def vstr2hex(version):
##     bits = []
##     n = [24,16,8,4,0]
##     r = 0
##     for s in version.split('.'):
##         r |= int(s) << n[0]
##         del n[0]
##     return r

def combine_paths(*args,**kws):
    """ Return a list of existing paths composed by all combinations of
        items from arguments.
    """
    r = []
    for a in args:
        if not a: continue
        if type(a) is types.StringType:
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
    if verbosity>1 and result:
        print '(','paths:',','.join(result),')'
    return result

def dict_append(d,**kws):
    for k,v in kws.items():
        if d.has_key(k):
            if k in ['library_dirs','include_dirs','define_macros']:
                [d[k].append(vv) for vv in v if vv not in d[k]]
            else:
                d[k].extend(v)
        else:
            d[k] = v

def show_all():
    import system_info
    import pprint
    match_info = re.compile(r'.*?_info').match
    for n in filter(match_info,dir(system_info)):
        if n in ['system_info','get_info']: continue
        c = getattr(system_info,n)()
        c.verbosity = 2
        r = c.get_info()

if __name__ == "__main__":
    show_all()
    print numpy_info().get_info()
    print numarray_info().get_info()

"""scipy_distutils

   Modified version of distutils to handle fortran source code, f2py,
   and other issues in the scipy build process.
"""

# Need to do something here to get distutils subsumed...

from scipy_distutils_version import scipy_distutils_version as __version__


from distutils.core import *
from distutils.core import setup as old_setup

from scipy_distutils.dist import Distribution
from scipy_distutils.extension import Extension
from scipy_distutils.command import build
from scipy_distutils.command import build_py
from scipy_distutils.command import config_compiler
from scipy_distutils.command import build_ext
from scipy_distutils.command import build_clib
from scipy_distutils.command import build_src
from scipy_distutils.command import sdist
from scipy_distutils.command import install_data
from scipy_distutils.command import install
from scipy_distutils.command import install_headers


def setup(**attr):

    distclass = Distribution
    cmdclass = {'build':            build.build,
                'build_src':        build_src.build_src,
                'config_fc':        config_compiler.config_fc,
                'build_ext':        build_ext.build_ext,
                'build_py':         build_py.build_py,                
                'build_clib':       build_clib.build_clib,
                'sdist':            sdist.sdist,
                'install_data':     install_data.install_data,
                'install':          install.install,
                'install_headers':  install_headers.install_headers
                }
    new_attr = attr.copy()
    if new_attr.has_key('cmdclass'):
        cmdclass.update(new_attr['cmdclass'])        
    new_attr['cmdclass'] = cmdclass
    
    if not new_attr.has_key('distclass'):
        new_attr['distclass'] = distclass    

    fortran_libraries = new_attr.get('fortran_libraries',[])
    if fortran_libraries:
        print 64*'*'+"""
    Using fortran_libraries setup option is depreciated
    ---------------------------------------------------
    Use libraries option instead. Yes, scipy_distutils
    now supports Fortran sources in libraries.
"""+64*'*'
        new_attr['libraries'].extend(fortran_libraries)
        del new_attr['fortran_libraries']

    return old_setup(**new_attr)


# http://www.pgroup.com

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

class PGroupFCompiler(FCompiler):

    compiler_type = 'pg'
    version_pattern =  r'\s*pg(f77|f90|hpf) (?P<version>[\d.-]+).*'

    executables = {
        'version_cmd'  : ["pgf77", "-V 2>/dev/null"],
        'compiler_f77' : ["pgf77"],
        'compiler_fix' : ["pgf90", "-Mfixed"],
        'compiler_f90' : ["pgf90"],
        'linker_so'    : ["pgf90","-shared"],
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
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='pg')
    compiler.customize()
    print compiler.get_version()

#!/usr/bin/env python
#
# exec_command
#
# Implements exec_command function that is (almost) equivalent to
# commands.getstatusoutput function but on NT, DOS systems the
# returned status is actually correct (though, the returned status
# values may be different by a factor). In addition, exec_command
# takes keyword arguments for (re-)defining environment variables.
#
# Provides functions:
#   exec_command  --- execute command in a specified directory and
#                     in the modified environment.
#   splitcmdline  --- inverse of ' '.join(argv)
#   find_executable --- locate a command using info from environment
#                     variable PATH. Equivalent to posix `which`
#                     command.
#
# Author: Pearu Peterson <pearu@cens.ioc.ee>
# Created: 11 January 2003
#
# Requires: Python 2.x
#
# Succesfully tested on:
#   os.name | sys.platform | comments
#   --------+--------------+----------
#   posix   | linux2       | Debian (sid) Linux, Python 2.1.3+, 2.2.3+, 2.3.3
#                            PyCrust 0.9.3, Idle 1.0.2
#   posix   | linux2       | Red Hat 9 Linux, Python 2.1.3, 2.2.2, 2.3.2
#   posix   | sunos5       | SunOS 5.9, Python 2.2, 2.3.2
#   posix   | darwin       | Darwin 7.2.0, Python 2.3
#   nt      | win32        | Windows Me
#                            Python 2.3(EE), Idle 1.0, PyCrust 0.7.2
#                            Python 2.1.1 Idle 0.8
#   nt      | win32        | Windows 98, Python 2.1.1. Idle 0.8
#   nt      | win32        | Cygwin 98-4.10, Python 2.1.1(MSC) - echo tests
#                            fail i.e. redefining environment variables may
#                            not work. FIXED: don't use cygwin echo!
#   posix   | cygwin       | Cygwin 98-4.10, Python 2.3.3(cygming special)

__all__ = ['exec_command','find_executable']

import os
import re
import sys
import tempfile

############################################################

try:
    import logging
    log = logging.getLogger('exec_command')
except ImportError:
    class logging:
        DEBUG = 0
        def info(self,message): print 'info:',message
        def warn(self,message): print 'warn:',message
        def debug(self,message): print 'debug:',message
        def basicConfig(self): pass
        def setLevel(self,level): pass
    log = logging = logging()

############################################################

def get_pythonexe():
    pythonexe = sys.executable
    if os.name in ['nt','dos']:
        fdir,fn = os.path.split(pythonexe)
        fn = fn.upper().replace('PYTHONW','PYTHON')
        pythonexe = os.path.join(fdir,fn)
        assert os.path.isfile(pythonexe),`pythonexe`+' is not a file'
    return pythonexe

############################################################

def splitcmdline(line):
    """ Inverse of ' '.join(sys.argv).
    """
    log.info('splitcmdline(%r)' % (line))
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
    assert l==['a','b','cc'],`l`
    l = splitcmdline('a')
    assert l==['a'],`l`
    l = splitcmdline('a "  b  cc"')
    assert l==['a','"  b  cc"'],`l`
    l = splitcmdline('"a bcc"  -h')
    assert l==['"a bcc"','-h'],`l`
    l = splitcmdline(r'"\"a \" bcc" -h')
    assert l==[r'"\"a \" bcc"','-h'],`l`
    l = splitcmdline(" 'a bcc'  -h")
    assert l==["'a bcc'",'-h'],`l`
    l = splitcmdline(r"'\'a \' bcc' -h")
    assert l==[r"'\'a \' bcc'",'-h'],`l`

############################################################

def find_executable(exe, path=None):
    """ Return full path of a executable.
    """
    log.info('find_executable(%r)' % exe)
    if path is None:
        path = os.environ.get('PATH',os.defpath)
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
        if os.name == 'nt':
            # Remove cygwin path components
            new_paths = []
            for path in paths:
                d,p = os.path.splitdrive(path)
                if p.lower().find('cygwin') >= 0:
                    log.debug('removing "%s" from PATH' % (path))
                else:
                    new_paths.append(path)
            paths = new_paths
    for path in paths:
        fn = os.path.join(path,exe)
        for s in suffices:
            f_ext = fn+s
            if os.path.isfile(f_ext) and os.access(f_ext,os.X_OK):
                log.debug('Found executable %s' % f_ext)
                return f_ext
    if not os.path.isfile(exe) or os.access(exe,os.X_OK):
        log.warn('Could not locate executable %s' % exe)
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
    log.info('exec_command(%r,%s)' % (command,\
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
        elif os.name=='posix' and sys.platform[:5]!='sunos':
            st = _exec_command_posix(command,
                                     use_shell=use_shell,
                                     use_tee=use_tee,
                                     **env)
        else:
            st = _exec_command(command, use_shell=use_shell, **env)
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

    if type(command) is type([]):
        command_str = ' '.join(command)
    else:
        command_str = command

    tmpfile = tempfile.mktemp()
    if use_tee:
        stsfile = tempfile.mktemp()
        filter = ''
        if use_tee == 2:
            filter = r'| tr -cd "\n" | tr "\n" "."; echo'
        command_posix = '( %s ; echo $? > %s ) 2>&1 | tee %s %s'\
                      % (command_str,stsfile,tmpfile,filter)
    else:
        command_posix = '%s > %s 2>&1' % (command_str,tmpfile)

    log.debug('Running os.system(%r)' % (command_posix))
    status = os.system(command_posix)

    if use_tee:
        if status:
            # if command_tee fails then fall back to robust exec_command
            log.warn('_exec_command_posix failed (status=%s)' % status)
            return _exec_command(command, use_shell=use_shell, **env)
        f = open(stsfile,'r')
        status = int(f.read())
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
    assert not status,`cmd`+' failed'
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


def _exec_command( command, use_shell=None, **env ):
    log.debug('_exec_command(...)')
    
    if use_shell is None:
        use_shell = os.name=='posix'

    using_command = 0
    if use_shell:
        # We use shell (unless use_shell==0) so that wildcards can be
        # used.
        sh = os.environ.get('SHELL','/bin/sh')
        if type(command) is type([]):
            argv = [sh,'-c'] + command
        else:
            argv = [sh,'-c',command]
    else:
        # On NT, DOS we avoid using command.com as it's exit status is
        # not related to the exit status of a command.
        if type(command) is type([]):
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
                argv = [os.environ['COMSPEC'],'/C']+argv
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

    so_flush()
    se_flush()
    os.dup2(fout.fileno(),so_fileno)
    if using_command:
        os.dup2(ferr.fileno(),se_fileno)
    else:
        os.dup2(fout.fileno(),se_fileno)

    try:
        status = spawn_command(os.P_WAIT,argv[0],argv,os.environ)
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
            status = 998
            if text:
                text = text + '\n'
            text = '%sCOMMAND %r FAILED: %s' %(text,command,errmess)

    if text[-1:]=='\n':
        text = text[:-1]
    if status is None:
        status = 0

    return status, text


def test_nt():
    pythonexe = get_pythonexe()

    if 1: ##  not (sys.platform=='win32' and os.environ.get('OSTYPE','')=='cygwin'):
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

def test_posix():
    s,o=exec_command("echo Hello")
    assert s==0 and o=='Hello',(s,o)

    s,o=exec_command('echo $AAA')
    assert s==0 and o=='',(s,o)

    s,o=exec_command('echo "$AAA"',AAA='Tere')
    assert s==0 and o=='Tere',(s,o)


    s,o=exec_command('echo "$AAA"')
    assert s==0 and o=='',(s,o)

    os.environ['BBB'] = 'Hi'
    s,o=exec_command('echo "$BBB"')
    assert s==0 and o=='Hi',(s,o)

    s,o=exec_command('echo "$BBB"',BBB='Hey')
    assert s==0 and o=='Hey',(s,o)

    s,o=exec_command('echo "$BBB"')
    assert s==0 and o=='Hi',(s,o)


    s,o=exec_command('this_is_not_a_command')
    assert s!=0 and o!='',(s,o)

    s,o=exec_command('echo path=$PATH')
    assert s==0 and o!='',(s,o)
    
    s,o=exec_command('python -c "import sys,os;sys.stderr.write(os.name)"')
    assert s==0 and o=='posix',(s,o)

    s,o=exec_command('python -c "raise \'Ignore me.\'"')
    assert s==1 and o,(s,o)

    s,o=exec_command('python -c "import sys;sys.stderr.write(\'0\');sys.stderr.write(\'1\');sys.stderr.write(\'2\')"')
    assert s==0 and o=='012',(s,o)

    s,o=exec_command('python -c "import sys;sys.exit(15)"')
    assert s==15 and o=='',(s,o)

    s,o=exec_command('python -c "print \'Heipa\'"')
    assert s==0 and o=='Heipa',(s,o)
    
    print 'ok'

def test_execute_in():
    pythonexe = get_pythonexe()
    tmpfile = tempfile.mktemp()
    fn = os.path.basename(tmpfile)
    tmpdir = os.path.dirname(tmpfile)
    f = open(tmpfile,'w')
    f.write('Hello')
    f.close()

    s,o = exec_command('%s -c "print \'Ignore following IOError:\',open(%r,\'r\')"' \
                       % (pythonexe,fn))
    assert s and o!='',(s,o)
    s,o = exec_command('%s -c "print open(%r,\'r\').read()"' % (pythonexe,fn),
                       execute_in = tmpdir)
    assert s==0 and o=='Hello',(s,o)
    os.remove(tmpfile)
    print 'ok'

if os.name=='posix':
    test = test_posix
elif os.name in ['nt','dos']:
    test = test_nt
else:
    raise NotImplementedError,'exec_command tests for '+os.name

############################################################

if __name__ == "__main__":
    logging.basicConfig()
    log.setLevel(logging.DEBUG)

    test_splitcmdline()
    test()
    test_execute_in()


import re
import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler
from exec_command import find_executable

class GnuFCompiler(FCompiler):

    compiler_type = 'gnu'
    version_pattern = r'GNU Fortran ((\(GCC[^\)]*(\)\)|\)))|)\s*'\
                      '(?P<version>[^\s*\)]+)'

    # 'g77 --version' results
    # SunOS: GNU Fortran (GCC 3.2) 3.2 20020814 (release)
    # Debian: GNU Fortran (GCC) 3.3.3 20040110 (prerelease) (Debian)
    #         GNU Fortran 0.5.25 20010319 (prerelease)
    # Redhat: GNU Fortran (GCC 3.2.2 20030222 (Red Hat Linux 3.2.2-5)) 3.2.2 20030222 (Red Hat Linux 3.2.2-5)

    for fc_exe in map(find_executable,['g77','f77']):
        if os.path.isfile(fc_exe):
            break
    executables = {
        'version_cmd'  : [fc_exe,"--version"],
        'compiler_f77' : [fc_exe,"-Wall","-fno-second-underscore"],
        'compiler_f90' : None,
        'compiler_fix' : None,
        'linker_so'    : [fc_exe],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"],
        }
    module_dir_switch = None
    module_include_switch = None
    if os.name != 'nt':
        pic_flags = ['-fPIC']

    def get_linker_so(self):
        # win32 linking should be handled by standard linker
        # Darwin g77 cannot be used as a linker.
        if re.match(r'(win32|cygwin.*|darwin)', sys.platform):
            return
        return FCompiler.get_linker_so(self)

    def get_flags_linker_so(self):
        opt = FCompiler.get_flags_linker_so(self)
        if not re.match(r'(win32|cygwin.*|darwin)', sys.platform):
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
        status, output = self.exec_command('%s -print-libgcc-file-name' \
                                           % (self.compiler_f77[0]),use_tee=0)        
        if not status:
            return os.path.dirname(output)
        return

    def get_library_dirs(self):
        opt = FCompiler.get_library_dirs(self)
        if sys.platform[:5] != 'linux':
            d = self.get_libgcc_dir()
            if d:
                opt.append(d)
        return opt

    def get_libraries(self):
        opt = FCompiler.get_libraries(self)
        d = self.get_libgcc_dir()
        if d is not None:
            for g2c in ['g2c-pic','g2c']:
                f = self.static_lib_format % (g2c, self.static_lib_extension)
                if os.path.isfile(os.path.join(d,f)):
                    break
        else:
            g2c = 'g2c'
        if sys.platform=='win32':
            opt.extend(['gcc',g2c])
        else:
            opt.append(g2c)
        return opt

    def get_flags_debug(self):
        return ['-g']

    def get_flags_opt(self):
        opt = ['-O3','-funroll-loops']
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
        march_flag = 1
        # 0.5.25 corresponds to 2.95.x
        if self.get_version() == '0.5.26': # gcc 3.0
            if cpu.is_AthlonK6():
                opt.append('-march=k6')
            elif cpu.is_AthlonK7():
                opt.append('-march=athlon')
            else:
                march_flag = 0
        # Note: gcc 3.2 on win32 has breakage with -march specified
        elif self.get_version() >= '3.1.1' \
            and not sys.platform=='win32': # gcc >= 3.1.1
            if cpu.is_AthlonK6():
                opt.append('-march=k6')
            elif cpu.is_AthlonK6_2():
                opt.append('-march=k6-2')
            elif cpu.is_AthlonK6_3():
                opt.append('-march=k6-3')
            elif cpu.is_AthlonK7():
                opt.append('-march=athlon')
            elif cpu.is_AthlonMP():
                opt.append('-march=athlon-mp')
                # there's also: athlon-tbird, athlon-4, athlon-xp
            elif cpu.is_PentiumIV():
                opt.append('-march=pentium4')
            elif cpu.is_PentiumIII():
                opt.append('-march=pentium3')
            elif cpu.is_PentiumII():
                opt.append('-march=pentium2')
            else:
                march_flag = 0
            if cpu.has_mmx(): opt.append('-mmmx')      
            if self.get_version() > '3.2.2':
                if cpu.has_sse2(): opt.append('-msse2')
                if cpu.has_sse(): opt.append('-msse')
            if cpu.has_3dnow(): opt.append('-m3dnow')
        else:
            march_flag = 0
        if march_flag:
            pass
        elif cpu.is_i686():
            opt.append('-march=i686')
        elif cpu.is_i586():
            opt.append('-march=i586')
        elif cpu.is_i486():
            opt.append('-march=i486')
        elif cpu.is_i386():
            opt.append('-march=i386')
        if cpu.is_Intel():
            opt.extend(['-malign-double','-fomit-frame-pointer'])
        return opt

if __name__ == '__main__':
    from scipy_distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='gnu')
    compiler.customize()
    print compiler.get_version()

"""
Support code for building Python extensions on Windows.

    # NT stuff
    # 1. Make sure libpython<version>.a exists for gcc.  If not, build it.
    # 2. Force windows to use gcc (we're struggling with MSVC and g77 support) 
    # 3. Force windows to use g77

"""

import os, sys
import distutils.ccompiler

# I'd really like to pull this out of scipy and make it part of distutils...
import scipy_distutils.command.build_flib as build_flib


if sys.platform == 'win32':
    # NT stuff
    # 1. Make sure libpython<version>.a exists for gcc.  If not, build it.
    # 2. Force windows to use gcc (we're struggling with MSVC and g77 support) 
    # 3. Force windows to use g77
    
    # 1.  Build libpython<version> from .lib and .dll if they don't exist.    
    import distutils.cygwinccompiler
    from distutils.version import StrictVersion
    from distutils.ccompiler import gen_preprocess_options, gen_lib_options
    from distutils.errors import DistutilsExecError, CompileError, UnknownFileError
    
    from distutils.unixccompiler import UnixCCompiler 
    
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
                out = os.popen('gcc' + ' -dumpversion','r')
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
                self.linker = 'dllwrap' + ' --driver-name g++'
            elif self.linker_dll == 'gcc':
                self.linker = 'g++'    

            # **changes: eric jones 4/11/01
            # 1. Check for import library on Windows.  Build if it doesn't exist.
            if not import_library_exists():
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
                self.set_executables(compiler='gcc -mno-cygwin -O2 -w',
                                     compiler_so='gcc -O2 -w -Wstrict-prototypes',
                                     linker_exe='g++ ',
                                     linker_so='g++ -shared')
            # added for python2.3 support
            # we can't pass it through set_executables because pre 2.2 would fail
            self.compiler_cxx = ['g++']
            
            # Maybe we should also append -mthreads, but then the finished
            # dlls need another dll (mingwm10.dll see Mingw32 docs)
            # (-mthreads: Support thread-safe exception handling on `Mingw32')       
            
            # no additional libraries needed 
            self.dll_libraries=[]
            
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

        def object_filenames (self,
                              source_filenames,
                              strip_dir=0,
                              output_dir=''):
            if output_dir is None: output_dir = ''
            print 'cygiwn_output_dir:', output_dir
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
                    print 'here', os.path.join (output_dir,
                                                base + self.obj_extension)
                    print '...:', output_dir, base + self.obj_extension                                            
                    obj_names.append (os.path.join (output_dir,
                                                base + self.obj_extension))
            return obj_names
    
        # object_filenames ()

        
    # On windows platforms, we want to default to mingw32 (gcc)
    # because msvc can't build blitz stuff.
    # We should also check the version of gcc available...
    #distutils.ccompiler._default_compilers['nt'] = 'mingw32'
    distutils.ccompiler._default_compilers = (('nt', 'mingw32'),) + \
                                distutils.ccompiler._default_compilers
    # reset the Mingw32 compiler in distutils to the one defined above
    distutils.cygwinccompiler.Mingw32CCompiler = Mingw32CCompiler
    
    def import_library_exists():
        """ on windows platforms, make sure a gcc import library exists
        """
        if os.name == 'nt':
            lib_name = "libpython%d%d.a" % tuple(sys.version_info[:2])
            full_path = os.path.join(sys.prefix,'libs',lib_name)
            if not os.path.exists(full_path):
                return 0
        return 1
    
    def build_import_library():
        """ Build the import libraries for Mingw32-gcc on Windows
        """
        from scipy_distutils import lib2def
        #libfile, deffile = parse_cmd()
        #if deffile is None:
        #    deffile = sys.stdout
        #else:
        #    deffile = open(deffile, 'w')
        lib_name = "python%d%d.lib" % tuple(sys.version_info[:2])    
        lib_file = os.path.join(sys.prefix,'libs',lib_name)
        def_name = "python%d%d.def" % tuple(sys.version_info[:2])    
        def_file = os.path.join(sys.prefix,'libs',def_name)
        nm_cmd = '%s %s' % (lib2def.DEFAULT_NM, lib_file)
        nm_output = lib2def.getnm(nm_cmd)
        dlist, flist = lib2def.parse_nm(nm_output)
        lib2def.output_def(dlist, flist, lib2def.DEF_HEADER, open(def_file, 'w'))
        
        out_name = "libpython%d%d.a" % tuple(sys.version_info[:2])
        out_file = os.path.join(sys.prefix,'libs',out_name)
        dll_name = "python%d%d.dll" % tuple(sys.version_info[:2])
        args = (dll_name,def_file,out_file)
        cmd = 'dlltool --dllname %s --def %s --output-lib %s' % args
        success = not os.system(cmd)
        # for now, fail silently
        if not success:
            print 'WARNING: failed to build import library for gcc. Linking will fail.'
        #if not success:
        #    msg = "Couldn't find import library, and failed to build it."
        #    raise DistutilsPlatformError, msg

"""distutils.extension

Provides the Extension class, used to describe C/C++ extension
modules in setup scripts.

Overridden to support f2py and SourceGenerator.
"""

# created 2000/05/30, Greg Ward

__revision__ = "$Id$"

from distutils.extension import Extension as old_Extension
from scipy_distutils.misc_util import SourceGenerator, SourceFilter

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
                  depends=None,
                  language=None,
                  f2py_options=None
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

        # Python 2.3 distutils new features
        self.depends = depends or []
        self.language = language

        self.f2py_options = f2py_options or []

    def has_cxx_sources(self):
        for source in self.sources:
            if isinstance(source,SourceGenerator) \
               or isinstance(source,SourceFilter):
                for s in source.sources:
                    if cxx_ext_re(s):
                        return 1
            if cxx_ext_re(str(source)):
                return 1
        return 0

    def has_f2py_sources(self):
        for source in self.sources:
            if isinstance(source,SourceGenerator) \
               or isinstance(source,SourceFilter):
                for s in source.sources:
                    if fortran_pyf_ext_re(s):
                        return 1
            elif fortran_pyf_ext_re(source):
                return 1
        return 0

    def generate_sources(self):
        new_sources = []
        for source in self.sources:
            if isinstance(source, SourceGenerator):
                new_sources.append(source.generate())
            elif isinstance(source, SourceFilter):
                new_sources.extend(source.filter())
            else:
                new_sources.append(source)
        self.sources = new_sources
                
    def get_sources(self):
        sources = []
        for source in self.sources:
            if isinstance(source,SourceGenerator):
                sources.extend(source.sources)
            elif isinstance(source,SourceFilter):
                sources.extend(source.sources)
            else:
                sources.append(source)
        return sources

# class Extension

#!/usr/bin/env python

import os
from glob import glob
from misc_util import get_path, default_config_dict, dot_join

def configuration(parent_package='',parent_path=None):
    package = 'scipy_distutils'
    local_path = get_path(__name__,parent_path)
    config = default_config_dict(package,parent_package)

    sub_package = dot_join(parent_package,package,'command')
    config['packages'].append(sub_package)
    config['package_dir'][sub_package] = os.path.join(local_path,'command')

    #for name in glob(os.path.join(local_path,'tests','*_ext')):
    #    p = dot_join(parent_package,package,'tests',os.path.basename(name))
    #    config['packages'].append(p)
    #    config['package_dir'][p] = name

    config['data_files'].append((package,[os.path.join(local_path,'sample_site.cfg')]))
    return config

if __name__ == '__main__':
    from scipy_distutils_version import scipy_distutils_version
    print 'scipy_distutils Version',scipy_distutils_version
    from core import setup
    config = configuration(parent_path='')
    for k,v in config.items():
        if not v:
            del config[k]
    setup(version = scipy_distutils_version,
          description = "Changes to distutils needed for SciPy "\
          "-- mostly Fortran support",
          author = "Travis Oliphant, Eric Jones, and Pearu Peterson",
          author_email = "scipy-dev@scipy.org",
          license = "SciPy License (BSD Style)",
          url = 'http://www.scipy.org',
          **config
          )

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

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
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='hpux')
    compiler.customize()
    print compiler.get_version()


#http://www.compaq.com/fortran/docs/

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

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

    module_dir_switch = None  #XXX Fix me
    module_include_switch = None #XXX Fix me

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

    compile_switch = '/c '
    object_switch = '/object:'
    library_switch = '/OUT:'      #No space after /OUT:!

    static_lib_extension = ".lib"
    static_lib_format = "%s%s"
    module_dir_switch = None  #XXX Fix me
    module_include_switch = None #XXX Fix me

    ar_exe = 'lib.exe'
    fc_exe = 'DF'
    if sys.platform=='win32':
        from distutils.msvccompiler import MSVCCompiler
        ar_exe = MSVCCompiler().lib

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
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='compaq')
    compiler.customize()
    print compiler.get_version()

major = 0
minor = 2
micro = 2
release_level = 'alpha'

from __cvs_version__ import cvs_version
cvs_minor = cvs_version[-3]
cvs_serial = cvs_version[-1]

scipy_distutils_version = '%(major)d.%(minor)d.%(micro)d_%(release_level)s'\
                          '_%(cvs_minor)d.%(cvs_serial)d' % (locals ())

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

class SunFCompiler(FCompiler):

    compiler_type = 'sun'
    version_pattern = r'(f90|f95): (Sun|Forte Developer 7) Fortran 95 (?P<version>[^\s]+).*'

    executables = {
        'version_cmd'  : ["f90", "-V"],
        'compiler_f77' : ["f90", "-f77", "-ftrap=%none"],
        'compiler_fix' : ["f90", "-fixed"],
        'compiler_f90' : ["f90"],
        'linker_so'    : ["f90","-Bdynamic","-G"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }
    module_dir_switch = '-moddir='
    module_include_switch = '-M'
    pic_flags = ['-xcode=pic32']

    def get_opt(self):
        return ['-fast','-dalign']
    def get_arch(self):
        return ['-xtarget=generic']
    def get_libraries(self):
        opt = FCompiler.get_libraries(self)
        opt.extend(['fsu','sunmath','mvec','f77compat'])
        return opt

if __name__ == '__main__':
    from scipy_distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='sun')
    compiler.customize()
    print compiler.get_version()

standalone = 1


import sys
from distutils.dist import Distribution as OldDistribution
from distutils.errors import DistutilsSetupError
from types import *

class Distribution (OldDistribution):

    if sys.version[:3]<'2.2':
        # For backward compatibility. Use libraries
        # instead of fortran_libraries.
        fortran_libraries = None

    def return_false(self):
        # Used by build_ext.run()
        return 0

    def check_data_file_list(self):
        """Ensure that the list of data_files (presumably provided as a
           command option 'data_files') is valid, i.e. it is a list of
           2-tuples, where the tuples are (name, list_of_libraries).
           Raise DistutilsSetupError if the structure is invalid anywhere;
           just returns otherwise."""
        print 'check_data_file_list'
        if type(self.data_files) is not ListType:
            raise DistutilsSetupError, \
                  "'data_files' option must be a list of tuples"

        for lib in self.data_files:
            if type(lib) is not TupleType and len(lib) != 2:
                raise DistutilsSetupError, \
                      "each element of 'data_files' must a 2-tuple"

            if type(lib[0]) is not StringType:
                raise DistutilsSetupError, \
                      "first element of each tuple in 'data_files' " + \
                      "must be a string (the package with the data_file)"

            if type(lib[1]) is not ListType:
                raise DistutilsSetupError, \
                      "second element of each tuple in 'data_files' " + \
                      "must be a list of files."
        return
   
    def get_data_files (self):
        print 'get_data_files'
        self.check_data_file_list()
        filenames = []
        
        # Gets data files specified
        for ext in self.data_files:
            filenames.extend(ext[1])

        return filenames

# http://developer.intel.com/software/products/compilers/flin/

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler, dummy_fortran_file
from exec_command import find_executable

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
        'compiler_f77' : [fc_exe,"-FI","-w90","-w95"],
        'compiler_fix' : [fc_exe,"-FI","-72"],
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

    def get_flags_opt(self):
        return ['-O3','-unroll']

    def get_flags_arch(self):
        opt = []
        if cpu.has_fdiv_bug():
            opt.append('-fdiv_check')
        if cpu.has_f00f_bug():
            opt.append('-0f_check')
        if cpu.is_PentiumPro() or cpu.is_PentiumII():
            opt.extend(['-tpp6','-xi'])
        elif cpu.is_PentiumIII():
            opt.append('-tpp6')
        elif cpu.is_Pentium():
            opt.append('-tpp5')
        elif cpu.is_PentiumIV():
            opt.extend(['-tpp7','-xW'])
        if cpu.has_mmx():
            opt.append('-xM')
        return opt

    def get_flags_linker_so(self):
        opt = FCompiler.get_flags_linker_so(self)
        v = self.get_version()
        if v and v >= '8.0':
            opt.append('-nofor_main')
        return opt

class IntelItaniumFCompiler(IntelFCompiler):
    compiler_type = 'intele'
    version_pattern = r'Intel\(R\) Fortran 90 Compiler Itanium\(TM\) Compiler'\
                      ' for the Itanium\(TM\)-based applications,'\
                      ' Version (?P<version>[^\s*]*)'

    for fc_exe in map(find_executable,['efort','efc','ifort']):
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
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='intel')
    compiler.customize()
    print compiler.get_version()



import os
from scipy_distutils.core import setup, Extension
from distutils.dep_util import newer

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

package = 'gen_ext'

def source_func(ext, src_dir):
    source = os.path.join(src_dir,'fib3.f')
    if newer(__file__, source):
        f = open(source,'w')
        f.write(fib3_f)
        f.close()
    return [source]

ext = Extension(package+'.fib3',[source_func])

setup(
    name = package,
    ext_modules = [ext],
    packages = [package+'.tests',package],
    package_dir = {package:'.'})




import os
from scipy_distutils.core import setup, Extension

package = 'f2py_f90_ext'

ext = Extension(package+'.foo',['src/foo_free.f90'])

setup(
    name = package,
    ext_modules = [ext],
    packages = [package+'.tests',package],
    package_dir = {package:'.'})




import os
from scipy_distutils.core import setup, Extension

ext = Extension('f2py_ext.fib2',['src/fib2.pyf','src/fib1.f'])

setup(
    name = 'f2py_ext',
    ext_modules = [ext],
    packages = ['f2py_ext.tests','f2py_ext'],
    package_dir = {'f2py_ext':'.'})




import os
from scipy_distutils.core import setup, Extension

ext_c = Extension('swig_ext._example',['src/example.i','src/example.c'])
ext_cpp = Extension('swig_ext._example2',['src/zoo.i','src/zoo.cc'],
                    depends=['src/zoo.h'],include_dirs=['src'])

setup(
    name = 'swig_ext',
    ext_modules = [ext_c,ext_cpp],
    packages = ['swig_ext.tests','swig_ext'],
    package_dir = {'swig_ext':'.'})


# Need to override the build command to include building of fortran libraries
# This class must be used as the entry for the build key in the cmdclass
#    dictionary which is given to the setup command.

__revision__ = "$Id$"

import sys, os
from distutils import util
from distutils.command.build import build as old_build

class build(old_build):

    sub_commands = [('config_fc',     lambda *args: 1), # new feature
                    ('build_src',     old_build.has_ext_modules), # new feature
                    ('build_py',      old_build.has_pure_modules),
                    ('build_clib',    old_build.has_c_libraries),
                    ('build_ext',     old_build.has_ext_modules),
                    ('build_scripts', old_build.has_scripts),
                   ]

    def get_plat_specifier(self):
        """ Return a unique string that identifies this platform.
            The string is used to build path names and contains no
            spaces or control characters. (we hope)
        """        
        plat_specifier = ".%s-%s" % (util.get_platform(), sys.version[0:3])
        
        #--------------------------------------------------------------------
        # get rid of spaces -- added for OS X support.
        # Use '_' like python2.3
        #--------------------------------------------------------------------
        plat_specifier = plat_specifier.replace(' ','_')
        
        #--------------------------------------------------------------------
        # make lower case ?? is this desired'
        #--------------------------------------------------------------------
        #plat_specifier = plat_specifier.lower()
        
        return plat_specifier
        
    def finalize_options (self):

        #--------------------------------------------------------------------
        # This line is re-factored to a function -- everything else in the
        # function is identical to the finalize_options function in the
        # standard distutils build.
        #--------------------------------------------------------------------
        #plat_specifier = ".%s-%s" % (get_platform(), sys.version[0:3])        
        plat_specifier = self.get_plat_specifier()
        
        # 'build_purelib' and 'build_platlib' just default to 'lib' and
        # 'lib.<plat>' under the base build directory.  We only use one of
        # them for a given distribution, though --
        if self.build_purelib is None:
            self.build_purelib = os.path.join(self.build_base, 'lib')
        if self.build_platlib is None:
            self.build_platlib = os.path.join(self.build_base,
                                              'lib' + plat_specifier)

        # 'build_lib' is the actual directory that we will use for this
        # particular module distribution -- if user didn't supply it, pick
        # one of 'build_purelib' or 'build_platlib'.
        if self.build_lib is None:
            if self.distribution.ext_modules:
                self.build_lib = self.build_platlib
            else:
                self.build_lib = self.build_purelib

        # 'build_temp' -- temporary directory for compiler turds,
        # "build/temp.<plat>"
        if self.build_temp is None:
            self.build_temp = os.path.join(self.build_base,
                                           'temp' + plat_specifier)
        if self.build_scripts is None:
            self.build_scripts = os.path.join(self.build_base,
                                              'scripts-' + sys.version[0:3])

    # finalize_options ()


import sys
from distutils.core import Command

#XXX: Implement confic_cc for enhancing C/C++ compiler options.

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
        ('help-fcompiler',None,"list available Fortran compilers"),
        ]

    boolean_options = ['debug','noopt','noarch','help-fcompiler']

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
        self.help_fcompiler = None
        return

    def finalize_options(self):
        if self.help_fcompiler:
            from scipy_distutils.fcompiler import show_fcompilers
            show_fcompilers(self.distribution)
            sys.exit()
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
from types import *

from distutils.dep_util import newer_group, newer
from distutils.command.build_ext import build_ext as old_build_ext

from scipy_distutils.command.build_clib import get_headers,get_directories
from scipy_distutils import misc_util, log
from scipy_distutils.misc_util import filter_sources, has_f_sources, has_cxx_sources

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

    def run(self):
        if not self.extensions:
            return

        if self.distribution.has_c_libraries():
            build_clib = self.get_finalized_command('build_clib')
            self.library_dirs.append(build_clib.build_clib)
        else:
            build_clib = None

        # Not including C libraries to the list of
        # extension libraries automatically to prevent
        # bogus linking commands. Extensions must
        # explicitly specify the C libraries that they use.

        save_mth = self.distribution.has_c_libraries
        self.distribution.has_c_libraries = self.distribution.return_false
        old_build_ext.run(self)   # sets self.compiler
        self.distribution.has_c_libraries = save_mth
        
        # Determine if Fortran compiler is needed.
        if build_clib and build_clib.fcompiler is not None:
            need_f_compiler = 1
        else:
            need_f_compiler = 0
            for ext in self.extensions:
                if has_f_sources(ext.sources):
                    need_f_compiler = 1
                    break

        # Determine if C++ compiler is needed.
        need_cxx_compiler = 0
        for ext in self.extensions:
            if has_cxx_sources(ext.sources):
                need_cxx_compiler = 1
                break

        # Initialize Fortran/C++ compilers if needed.
        if need_f_compiler:
            from scipy_distutils.fcompiler import new_fcompiler
            self.fcompiler = new_fcompiler(compiler=self.fcompiler,
                                           verbose=self.verbose,
                                           dry_run=self.dry_run,
                                           force=self.force)
            self.fcompiler.customize(self.distribution)
            self.fcompiler.customize_cmd(self)
        if need_cxx_compiler:
            c = self.compiler
            if c.compiler[0].find('gcc')>=0:
                if sys.version[:3]>='2.3':
                    if not c.compiler_cxx:
                        c.compiler_cxx = [c.compiler[0].replace('gcc','g++')]\
                                         + c.compiler[1:]
                else:
                    c.compiler_cxx = [c.compiler[0].replace('gcc','g++')]\
                                     + c.compiler[1:]
            else:
                print 'XXX: Fix compiler_cxx for',c.__class__.__name__

        # Build extensions
        self.build_extensions2()
        return

    def build_extensions(self):
        # Hold on building extensions in old_build_ext.run()
        # until Fortran/C++ compilers are set. Building will be
        # carried out in build_extensions2()
        return

    def build_extensions2(self):
        old_build_ext.build_extensions(self)
        return

    def swig_sources(self, sources):
        # Do nothing. Swig sources have beed handled in build_src command.
        return sources

    def build_extension(self, ext):
        sources = ext.sources
        if sources is None or type(sources) not in (ListType, TupleType):
            raise DistutilsSetupError, \
                  ("in 'ext_modules' option (extension '%s'), " +
                   "'sources' must be present and must be " +
                   "a list of source filenames") % ext.name
        sources = list(sources)

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

        c_sources, cxx_sources, f_sources, fmodule_sources = filter_sources(ext.sources)

        if sys.version[:3]>='2.3':
            kws = {'depends':ext.depends}
        else:
            kws = {}
        c_objects = self.compiler.compile(c_sources,
                                          output_dir=self.build_temp,
                                          macros=macros,
                                          include_dirs=ext.include_dirs,
                                          debug=self.debug,
                                          extra_postargs=extra_args,
                                          **kws)
        if cxx_sources:
            old_compiler = self.compiler.compiler_so[0]
            self.compiler.compiler_so[0] = self.compiler.compiler_cxx[0]
            c_objects += self.compiler.compile(cxx_sources,
                                              output_dir=self.build_temp,
                                              macros=macros,
                                              include_dirs=ext.include_dirs,
                                              debug=self.debug,
                                              extra_postargs=extra_args,
                                              **kws)
            self.compiler.compiler_so[0] = old_compiler

        check_for_f90_modules = not not fmodule_sources

        if f_sources or fmodule_sources:
            extra_postargs = []
            include_dirs = ext.include_dirs[:]
            module_dirs = [] # XXX Figure out how users could change this?

            if check_for_f90_modules:
                module_build_dir = os.path.join(\
                    self.build_temp,os.path.dirname(\
                    self.get_ext_filename(fullname)))

                self.mkpath(module_build_dir)
                if self.fcompiler.module_dir_switch is None:
                    existing_modules = glob('*.mod')
                extra_postargs += self.fcompiler.module_options(\
                    module_dirs,module_build_dir)

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
                    self.move_file(f, module_build_dir)

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

        old_linker_so_0 = self.compiler.linker_so[0]

        use_fortran_linker = 0
        if f_sources:
            use_fortran_linker = 1
        elif self.distribution.has_c_libraries():            
            build_clib = self.get_finalized_command('build_clib')
            f_libs = []
            for (lib_name, build_info) in build_clib.libraries:
                if has_f_sources(build_info.get('sources',[])):
                    f_libs.append(lib_name)
            for l in ext.libraries:
                if l in f_libs:
                    use_fortran_linker = 1
                    break

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
             libraries=self.get_libraries(ext),
             library_dirs=ext.library_dirs,
             runtime_library_dirs=ext.runtime_library_dirs,
             extra_postargs=extra_args,
             export_symbols=self.get_export_symbols(ext),
             debug=self.debug,
             build_temp=self.build_temp,**kws)

        self.compiler.linker_so[0] = old_linker_so_0
        return

    def get_source_files (self):
        self.check_extensions_list(self.extensions)
        filenames = []
        def visit_func(filenames,dirname,names):
            if os.path.basename(dirname)=='CVS':
                return
            for name in names:
                fullname = os.path.join(dirname,name)
                if os.path.isfile(fullname):
                    filenames.append(fullname)
        # Get sources and any include files in the same directory.
        for ext in self.extensions:
            sources = filter(lambda s:type(s) is StringType,ext.sources)
            filenames.extend(sources)
            filenames.extend(get_headers(get_directories(sources)))
            for d in ext.depends:
                if is_local_src_dir(d):
                    os.path.walk(d,visit_func,filenames)
                elif os.path.isfile(d):
                    filenames.append(d)
        return filenames

def is_local_src_dir(directory):
    """ Return true if directory is local directory.
    """
    abs_dir = os.path.abspath(directory)
    c = os.path.commonprefix([os.getcwd(),abs_dir])
    new_dir = abs_dir[len(c):].split(os.sep)
    if new_dir and not new_dir[0]:
        new_dir = new_dir[1:]
    if new_dir and new_dir[0]=='build':
        return 0
    new_dir = os.sep.join(new_dir)
    return os.path.isdir(new_dir)

"""
    I don't know much about this one, so I'm not going to mess with 
    it much. (eric)
"""
from distutils.command.install import *
from distutils.command.install_headers import install_headers as old_install_headers

class install_headers (old_install_headers):
    def run (self):
        headers = self.distribution.headers
        if not headers:
            return
        # hack to force headers into Numeric instead of SciPy
        import os
        d,f = os.path.split(self.install_dir)
        self.install_dir = os.path.join(d,'Numeric')        
        self.mkpath(self.install_dir)
        for header in headers:
            (out, _) = self.copy_file(header, self.install_dir)
            self.outfiles.append(out)    


from distutils.command.build_py import build_py as old_build_py

class build_py(old_build_py):

    def find_package_modules(self, package, package_dir):
        modules = old_build_py.find_package_modules(self, package, package_dir)

        # Find build_src generated *.py files.
        build_src = self.get_finalized_command('build_src')
        modules += build_src.py_modules.get(package,[])

        return modules

""" Build swig, f2py, weave, sources.
"""

import os
import re

from distutils.cmd import Command
from distutils.command import build_ext, build_py
from distutils.util import convert_path
from distutils.dep_util import newer_group, newer

from scipy_distutils import log
from scipy_distutils.misc_util import fortran_ext_match


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
        self.build_src = None
        self.build_lib = None
        self.build_base = None
        self.force = None
        self.inplace = 0
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
        self.py_modules = self.distribution.py_modules
        if self.build_src is None:
            self.build_src = os.path.join(self.build_base, 'src')

        # py_modules is used in build_py.find_package_modules
        self.py_modules = {}

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
        if not self.extensions:
            return
        self.build_sources()
        return

    def build_sources(self):
        self.check_extensions_list(self.extensions)

        for ext in self.extensions:
            self.build_extension_sources(ext)
        return

    def build_extension_sources(self, ext):
        fullname = self.get_ext_fullname(ext.name)
        modpath = fullname.split('.')
        package = '.'.join(modpath[0:-1])

        sources = list(ext.sources)

        sources = self.generate_sources(sources, ext)

        sources = self.swig_sources(sources, ext)

        sources = self.f2py_sources(sources, ext)

        sources, py_files = self.filter_py_files(sources)

        if not self.py_modules.has_key(package):
            self.py_modules[package] = []
        modules = []
        for f in py_files:
            module = os.path.splitext(os.path.basename(f))[0]
            modules.append((package, module, f))
        self.py_modules[package] += modules

        ext.sources = sources
        return

    def generate_sources(self, sources, extension):
        new_sources = []
        func_sources = []
        for source in sources:
            if type(source) is type(''):
                new_sources.append(source)
            else:
                func_sources.append(source)
        if not func_sources:
            return new_sources
        if self.inplace:
            build_dir = '.'
        else:
            build_dir = self.build_src
        self.mkpath(build_dir)
        for func in func_sources:
            source = func(extension, build_dir)
            if type(source) is type([]):
                [log.info('  adding %s to sources.' % (s)) for s in source]
                new_sources.extend(source)
            else:
                log.info('  adding %s to sources.' % (source))
                new_sources.append(source)
        return new_sources

    def filter_py_files(self, sources):
        new_sources = []
        py_files = []
        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext=='.py':        
                py_files.append(source)
            else:
                new_sources.append(source)
        return new_sources, py_files

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
                    target_dir = os.path.join(self.build_src,
                                              os.path.dirname(base))
                if os.path.isfile(source):
                    name = get_f2py_modulename(source)
                    assert name==ext_name,'mismatch of extension names: '\
                           +source+' provides'\
                           ' '+`name`+' but expected '+`ext_name`
                    target_file = os.path.join(target_dir,name+'module.c')
                else:
                    log.info('  source %s does not exist: skipping f2py\'ing.' \
                             % (source))
                    name = ext_name
                    skip_f2py = 1
                    target_file = os.path.join(target_dir,name+'module.c')
                    if not os.path.isfile(target_file):
                        log.info('  target %s does not exist:\n   '\
                                 'Assuming %smodule.c was generated with '\
                                 '"build_src --inplace" command.' \
                                 % (target_file, name))
                        target_dir = os.path.dirname(base)
                        target_file = os.path.join(target_dir,name+'module.c')
                        assert os.path.isfile(target_file),`target_file`+' missing'
                        log.info('   Yes! Using %s as up-to-date target.' \
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

        f2py_options = self.f2pyflags[:]
        if f2py_sources:
            assert len(f2py_sources)==1,\
                   'only one .pyf file is allowed per extension module but got'\
                   ' more:'+`f2py_sources`
            source = f2py_sources[0]
            target_file = f2py_targets[source]
            target_dir = os.path.dirname(target_file)
            depends = [source] + extension.depends
            if (self.force or newer_group(depends, target_file,'newer')) \
                   and not skip_f2py:
                log.info("  f2py'ing %s", source)
                import f2py2e
                f2py2e.run_main(f2py_options + ['--build-dir',target_dir,source])
            else:
                log.info("  skipping '%s' f2py interface (up-to-date)" % (source))
        else:
            #XXX TODO: --inplace support for sdist command
            target_dir = self.build_src
            target_file = os.path.join(target_dir,ext_name + 'module.c')
            new_sources.append(target_file)
            depends = f_sources + extension.depends
            if (self.force or newer_group(depends, target_file, 'newer')) \
                   and not skip_f2py:
                import f2py2e
                log.info("  f2py'ing fortran files for '%s'" % (target_file))
                self.mkpath(target_dir)
                f2py2e.run_main(f2py_options + ['--lower',
                                                '--build-dir',target_dir]+\
                                ['-m',ext_name]+f_sources)
            else:
                log.info("  skipping f2py fortran files for '%s' (up-to-date)" % (target_file))

        assert os.path.isfile(target_file),`target_file`+' missing'

        target_c = os.path.join(self.build_src,'fortranobject.c')
        target_h = os.path.join(self.build_src,'fortranobject.h')
        log.info('  adding %s to sources.' % (target_c))
        new_sources.append(target_c)
        if self.build_src not in extension.include_dirs:
            log.info("  adding %s to extension '%s' include_dirs."\
                     % (self.build_src,extension.name))
            extension.include_dirs.append(self.build_src)

        if not skip_f2py:
            import f2py2e
            d = os.path.dirname(f2py2e.__file__)
            source_c = os.path.join(d,'src','fortranobject.c')
            source_h = os.path.join(d,'src','fortranobject.h')
            if newer(source_c,target_c) or newer(source_h,target_h):
                self.mkpath(os.path.dirname(target_c))
                self.copy_file(source_c,target_c)
                self.copy_file(source_h,target_h)
        else:
            assert os.path.isfile(target_c),`target_c` + ' missing'
            assert os.path.isfile(target_h),`target_h` + ' missing'
   
        for name_ext in ['-f2pywrappers.f','-f2pywrappers2.f90']:
            filename = os.path.join(target_dir,ext_name + name_ext)
            if os.path.isfile(filename):
                log.info('  adding %s to sources.' % (filename))
                f_sources.append(filename)

        return new_sources + f_sources

    def swig_sources(self, sources, extension):
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
                else:
                    target_dir = os.path.join(self.build_src,
                                              os.path.dirname(base))
                if os.path.isfile(source):
                    name = get_swig_modulename(source)
                    assert name==ext_name[1:],'mismatch of extension names: '\
                           +source+' provides'\
                           ' '+`name`+' but expected '+`ext_name[1:]`
                    if typ is None:
                        typ = get_swig_target(source)
                        is_cpp = typ=='c++'
                        if is_cpp:
                            target_ext = '.cpp'
                    else:
                        assert typ == get_swig_target(source),`typ`
                    target_file = os.path.join(target_dir,'%s_wrap%s' \
                                               % (name, target_ext))
                else:
                    log.info('  source %s does not exist: skipping swig\'ing.' \
                             % (source))
                    name = ext_name[1:]
                    skip_swig = 1
                    target_file = _find_swig_target(target_dir, name)
                    if not os.path.isfile(target_file):
                        log.info('  target %s does not exist:\n   '\
                                 'Assuming %s_wrap.{c,cpp} was generated with '\
                                 '"build_src --inplace" command.' \
                                 % (target_file, name))
                        target_dir = os.path.dirname(base)
                        target_file = _find_swig_target(target_dir, name)
                        assert os.path.isfile(target_file),`target_file`+' missing'
                        log.info('   Yes! Using %s as up-to-date target.' \
                                 % (target_file))
                target_dirs.append(target_dir)
                new_sources.append(target_file)
                py_files.append(os.path.join(target_dir,name+'.py'))
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
                log.info("  swigging %s to %s", source, target)
                self.spawn(swig_cmd + self.swigflags + ["-o", target, source])
            else:
                log.info("  skipping '%s' swig interface (up-to-date)" \
                         % (source))

        return new_sources + py_files

#### SWIG related auxiliary functions ####
_swig_module_name_match = re.compile(r'\s*%module\s*(?P<name>[\w_]+)',
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

__revision__ = "$Id$"

distutils_all = [  'build_py',
                   'build_scripts',
                   'clean',
                   'install_lib',
                   'install_scripts',
                   'bdist',
                   'bdist_dumb',
                   'bdist_rpm',
                   'bdist_wininst',
                ]

__import__('distutils.command',globals(),locals(),distutils_all)

__all__ = ['build',
           'config_compiler',
           'build_src',
           'build_ext',
           'build_clib',
           'install',
           'install_data',
           'install_headers',
           'sdist',
          ] + distutils_all


import os
import sys

from distutils.command.sdist import *
from distutils.command.sdist import sdist as old_sdist
from scipy_distutils import log
from scipy_distutils import line_endings

class sdist(old_sdist):
    def add_defaults (self):
        old_sdist.add_defaults(self)

        if self.distribution.has_data_files():
            self.filelist.extend(self.distribution.get_data_files())

    def make_release_tree (self, base_dir, files):
        """Create the directory tree that will become the source
        distribution archive.  All directories implied by the filenames in
        'files' are created under 'base_dir', and then we hard link or copy
        (if hard linking is unavailable) those files into place.
        Essentially, this duplicates the developer's source tree, but in a
        directory named after the distribution, containing only the files
        to be distributed.
        """
        # Create all the directories under 'base_dir' necessary to
        # put 'files' there; the 'mkpath()' is just so we don't die
        # if the manifest happens to be empty.
        
        dest_files = remove_common_base(files)
        self.mkpath(base_dir)
        dir_util.create_tree(base_dir, dest_files,
                             verbose=self.verbose, dry_run=self.dry_run)

        # And walk over the list of files, either making a hard link (if
        # os.link exists) to each one that doesn't already exist in its
        # corresponding location under 'base_dir', or copying each file
        # that's out-of-date in 'base_dir'.  (Usually, all files will be
        # out-of-date, because by default we blow away 'base_dir' when
        # we're done making the distribution archives.)
    
        if hasattr(os, 'link'):        # can make hard links on this system
            link = 'hard'
            msg = "making hard links in %s..." % base_dir
        else:                           # nope, have to copy
            link = None
            msg = "copying files to %s..." % base_dir

        if not files:
            log.warn("no files to distribute -- empty manifest?")
        else:
            log.info(msg)
        
        dest_files = [os.path.join(base_dir,file) for file in dest_files]
        file_pairs = zip(files,dest_files)    
        for file,dest in file_pairs:
            if not os.path.isfile(file):
                log.warn("'%s' not a regular file -- skipping", file)
            else:
                #ej: here is the only change -- made to handle
                # absolute paths to files as well as relative
                #par,file_name = os.path.split(file)
                #dest = os.path.join(base_dir, file_name)
                # end of changes
                
                # old code
                #dest = os.path.join(base_dir, file)
                #end old code
                self.copy_file(file, dest, link=link)

        self.distribution.metadata.write_pkg_info(base_dir)
        #raise ValueError
    # make_release_tree ()

    def make_distribution (self):
        """ Overridden to force a build of zip files to have Windows line 
            endings and tar balls to have Unix line endings.
            
            Create the source distribution(s).  First, we create the release
            tree with 'make_release_tree()'; then, we create all required
            archive files (according to 'self.formats') from the release tree.
            Finally, we clean up by blowing away the release tree (unless
            'self.keep_temp' is true).  The list of archive files created is
            stored so it can be retrieved later by 'get_archive_files()'.
        """
        # Don't warn about missing meta-data here -- should be (and is!)
        # done elsewhere.
        base_dir = self.distribution.get_fullname()
        base_name = os.path.join(self.dist_dir, base_dir)
        files = map(os.path.abspath, self.filelist.files)
        self.make_release_tree(base_dir, files)
        archive_files = []              # remember names of files we create
        for fmt in self.formats:            
            self.convert_line_endings(base_dir,fmt)
            file = self.make_archive(base_name, fmt, base_dir=base_dir)
            archive_files.append(file)
                    
        self.archive_files = archive_files

        if not self.keep_temp:
            dir_util.remove_tree(base_dir, self.verbose, self.dry_run)

    def convert_line_endings(self,base_dir,fmt):
        """ Convert all text files in a tree to have correct line endings.
            
            gztar --> \n   (Unix style)
            zip   --> \r\n (Windows style)
        """
        if fmt == 'gztar':
            line_endings.dos2unix_dir(base_dir)
        elif fmt == 'zip':
            line_endings.unix2dos_dir(base_dir)
            
def remove_common_base(files):
    """ Remove the greatest common base directory from all the
        absolute file paths in the list of files.  files in the
        list without a parent directory are not affected.
    """
    rel_files = filter(lambda x: not os.path.dirname(x),files)
    abs_files = filter(os.path.dirname,files)
    base = find_common_base(abs_files)
    # will leave files with local path unaffected
    # and maintains original file order
    results = [file[len(base):] for file in files]
    return results

def find_common_base(files):
    """ Find the "greatest common base directory" of a list of files
    """
    if not files:
        return ''
    result = ''
    d,f = os.path.split(files[0])
    keep_looking = 1    
    while(keep_looking and d):
        keep_looking = 0
        for file in files:
            if string.find('start'+file,'start'+d) == -1:
                keep_looking = 1
                break
        if keep_looking:
            d,f = os.path.split(d)
        else:
            result = d
            
    if d: 
        d = os.path.join(d,'')
    return d        

""" Modified version of build_clib that handles fortran source files.
"""

import os
import string
import sys
import re
from glob import glob
from types import *
from distutils.command.build_clib import build_clib as old_build_clib
from distutils.command.build_clib import show_compilers

from scipy_distutils import log
from distutils.dep_util import newer_group
from scipy_distutils.misc_util import filter_sources, has_f_sources

def get_headers(directory_list):
    # get *.h files from list of directories
    headers = []
    for dir in directory_list:
        head = glob(os.path.join(dir,"*.h")) #XXX: *.hpp files??
        headers.extend(head)

    return headers

def get_directories(list_of_sources):
    # get unique directories from list of sources.
    direcs = []
    for file in list_of_sources:
        dir = os.path.split(file)
        if dir[0] != '' and not dir[0] in direcs:
            direcs.append(dir[0])

    return direcs

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

        #XXX: This is hackish and probably unnecessary,
        #     could we get rid of this?
        from scipy_distutils import misc_util
        extra_includes = misc_util.get_environ_include_dirs()
        if extra_includes:
            print "XXX: are you sure you'll need PYTHONINCLUDES env. variable??"
        self.include_dirs.extend(extra_includes)

        return

    def have_f_sources(self):
        for (lib_name, build_info) in self.libraries:
            if has_f_sources(build_info.get('sources',[])):
                return 1
        return 0

    def run(self):
        if not self.libraries:
            return
        old_build_clib.run(self)   # sets self.compiler
        if self.have_f_sources():
            from scipy_distutils.fcompiler import new_fcompiler
            self.fcompiler = new_fcompiler(compiler=self.fcompiler,
                                           verbose=self.verbose,
                                           dry_run=self.dry_run,
                                           force=self.force)
            self.fcompiler.customize(self.distribution)

        #XXX: C++ linker support, see build_ext2.py

        self.build_libraries2(self.libraries)
        return

    def build_libraries(self, libraries):
        # Hold on building libraries in old_build_clib.run()
        # until Fortran/C++ compilers are set. Building will be
        # carried out in build_libraries2()
        return

    def get_source_files(self):
        if sys.version[:3]>='2.2':
            filenames = old_build_clib.get_source_files(self)
        else:
            for (lib_name, build_info) in self.libraries:
                filenames.extend(build_info.get('sources',[]))
        filenames.extend(get_headers(get_directories(filenames)))
        return filenames

    def build_libraries2(self, libraries):

        compiler = self.compiler
        fcompiler = self.fcompiler

        for (lib_name, build_info) in libraries:
            sources = build_info.get('sources')
            if sources is None or type(sources) not in (ListType, TupleType):
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

            macros = build_info.get('macros')
            include_dirs = build_info.get('include_dirs')

            c_sources, cxx_sources, f_sources, fmodule_sources \
                       = filter_sources(sources)

            if fmodule_sources:
                print 'XXX: Fortran 90 module support not implemented or tested'
                f_sources.extend(fmodule_sources)

            if cxx_sources:
                print 'XXX: C++ linker support not implemented or tested'
            objects = compiler.compile(c_sources+cxx_sources,
                                       output_dir=self.build_temp,
                                       macros=macros,
                                       include_dirs=include_dirs,
                                       debug=self.debug)

            if f_sources:
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
        return

from types import StringType
from distutils.command.install import *
from distutils.command.install import install as old_install
from distutils.util import convert_path
from distutils.file_util import write_file
from distutils.errors import DistutilsOptionError
from scipy_distutils import log

#install support for Numeric.pth setup

class install(old_install):

    def finalize_options (self):
        old_install.finalize_options(self)
        self.install_lib = self.install_libbase
        
    def handle_extra_path (self):
        if self.extra_path is None:
            self.extra_path = self.distribution.extra_path

        if self.extra_path is not None:
            if type(self.extra_path) is StringType:
                self.extra_path = string.split(self.extra_path, ',')
            if len(self.extra_path) == 1:
                path_file = extra_dirs = self.extra_path[0]
            elif len(self.extra_path) == 2:
                (path_file, extra_dirs) = self.extra_path
            else:
                raise DistutilsOptionError, \
                      "'extra_path' option must be a list, tuple, or " + \
                      "comma-separated string with 1 or 2 elements"

            # convert to local form in case Unix notation used (as it
            # should be in setup scripts)
            extra_dirs = convert_path(extra_dirs)

        else:
            path_file = None
            extra_dirs = ''

        # XXX should we warn if path_file and not extra_dirs? (in which
        # case the path file would be harmless but pointless)
        self.path_file = path_file
        self.extra_dirs = ''
        self.pth_file = extra_dirs

    # handle_extra_path ()

    def create_path_file (self):
        filename = os.path.join(self.install_libbase,
                                self.path_file + ".pth")
        if self.install_path_file:
            self.execute(write_file,
                         (filename, [self.pth_file]),
                         "creating %s" % filename)
        else:
            log.warn("path file '%s' not created" % filename)

from distutils.command.install_data import *
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

