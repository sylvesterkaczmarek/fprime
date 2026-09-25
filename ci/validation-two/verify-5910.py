from pathlib import Path
import os, re, subprocess
root=Path.cwd()
logs=Path(os.environ.get('VALIDATION_LOG_DIR','/task'))
logs.mkdir(parents=True,exist_ok=True)
build=os.environ.get('CFDP_BUILD','build-clang')
base=os.environ.get('BASE_SHA','0d4156ef9d685f2357008f1cbcf34bd3b3c10ecd')
helper=root/'Svc/Ccsds/CfdpManager/test/ut/CfdpManagerHelperTests.cpp'
clist=root/'Svc/Ccsds/CfdpManager/Clist.cpp'
tx=root/'Svc/Ccsds/CfdpManager/TransactionTx.cpp'
params=root/'Svc/Ccsds/CfdpManager/Parameters.fppi'
paths=[helper,clist,tx,params]
backups={p:p.read_bytes() for p in paths}
def write(p,data):
    t=p.with_name(p.name+'.tmp');t.write_bytes(data);t.replace(p)
def run(args,label,expected=0,env=None):
    e=os.environ.copy();e.update({'ASAN_OPTIONS':'halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
    if env:e.update(env)
    proc=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=e)
    (logs/(label+'.log')).write_text(proc.stdout)
    if (proc.returncode==0)!=(expected==0):
        print(proc.stdout[-10000:]);raise RuntimeError(f'{label}: exit {proc.returncode}, expected {expected}')
    print(label, 'PASS' if proc.returncode==0 else 'EXPECTED FAILURE', flush=True)
    return proc.stdout
def compile(label):
    run(['cmake','--build',build,'--target','Svc_Ccsds_CfdpManager_ut_exe','Svc_Ccsds_CfdpManager_Types_ut_exe','-j4'],label)
def tests(label,filt=None,expected=0,types=False):
    args=['ctest','--test-dir',build+'/F-Prime/Svc/Ccsds/CfdpManager','--no-tests=error','-V']
    if not types:args+=['-R','^Svc_Ccsds_CfdpManager_ut_exe$']
    return run(args,label,expected,{'GTEST_FILTER':filt} if filt else None)
try:
    compile('formatted-build-5910')
    tests('formatted-full-5910',types=True)
    # Same deliberately broken implementation, old versus strengthened tests.
    mutant=re.sub(rb'if \(!CfdpCListTraverseStatusIsContinue\(fn\(node, context\)\)\) \{\s*break;\s*\}',b'(void)fn(node, context);',backups[clist])
    assert mutant!=backups[clist] and mutant.count(b'(void)fn(node, context);')==2
    write(clist,mutant)
    original=subprocess.check_output(['git','show',base+':'+str(helper.relative_to(root))])
    write(helper,original)
    compile('mutant-old-build-5910')
    tests('mutant-old-early-exit-5910','ClistHelper.TraverseForwardEarlyExit:ClistHelper.TraverseReverseEarlyExit')
    write(helper,backups[helper]);compile('mutant-new-build-5910')
    out=tests('mutant-new-early-exit-5910','ClistHelper.TraverseForwardEarlyExit:ClistHelper.TraverseReverseEarlyExit',1)
    assert '[  FAILED  ] ClistHelper.TraverseForwardEarlyExit' in out and '[  FAILED  ] ClistHelper.TraverseReverseEarlyExit' in out
    write(clist,backups[clist])
    # Ignore the configured retry budget: the behavioral test must detect this.
    needle=b'this->m_cfdpManager->getPostInactivitySendRetriesParam()'
    assert backups[tx].count(needle)==1
    write(tx,backups[tx].replace(needle,b'static_cast<U8>(3)'))
    compile('mutant-retry-build-5910')
    tests('mutant-retry-budget-5910','PostInactivityRetries.PendingSendBudget',1)
    write(tx,backups[tx])
    # The previous default-value test gap is checked independently.
    needle=b'param PostInactivitySendRetries: U8 \\\n    default 3'
    assert backups[params].count(needle)==1
    write(params,backups[params].replace(needle,needle[:-1]+b'4'))
    compile('mutant-default-build-5910')
    tests('mutant-old-parameters-5910','Parameter.*')
    tests('mutant-default-value-5910','PostInactivityRetries.DefaultValue',1)
    write(params,backups[params])
    compile('restored-build-5910')
    out=tests('restored-full-5910',types=True)
    for line in out.splitlines():
        if '[  PASSED  ]' in line or '100% tests passed' in line: print(line,flush=True)
finally:
    for p,data in backups.items():write(p,data)
