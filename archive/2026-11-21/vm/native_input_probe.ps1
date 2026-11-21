
$ErrorActionPreference='Stop'
$r=Join-Path $env:USERPROFILE 'mas-task-handoff-verification'
$n='AUTO-MAS-Native-Input-Probe-'+[guid]::NewGuid().ToString('N')
$log=Join-Path $r 'native_input_probe.log'
if(Test-Path $log){Remove-Item -LiteralPath $log}
$a=New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c .venv\Scripts\python.exe native_input_probe.py > native_input_probe.log 2>&1' -WorkingDirectory $r
$principal=New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive
Register-ScheduledTask -TaskName $n -Action $a -Principal $principal | Out-Null
try {
    Start-ScheduledTask -TaskName $n
    Start-Sleep -Seconds 2
    $deadline=(Get-Date).AddSeconds(100)
    while((Get-ScheduledTask -TaskName $n).State -eq 'Running' -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 1}
    $status=Get-ScheduledTaskInfo -TaskName $n
    if(Test-Path $log){Get-Content -LiteralPath $log}
    Write-Output "task_result=$($status.LastTaskResult)"
    exit $status.LastTaskResult
} finally {
    if((Get-ScheduledTask -TaskName $n).State -eq 'Running'){Stop-ScheduledTask -TaskName $n}
    Unregister-ScheduledTask -TaskName $n -Confirm:$false
}
