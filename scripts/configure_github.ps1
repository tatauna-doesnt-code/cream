param([switch]$PlanOnly)
$ErrorActionPreference = 'Stop'
$creamRepo = 'tatauna-doesnt-code/cream'
if ($PlanOnly) {
    Get-Content -LiteralPath (Join-Path $PSScriptRoot '../docs/github-settings-plan.md')
    return
}
$creamSecret = Read-Host 'Repository-limited GitHub administration token (never the CREAM update token)' -AsSecureString
$creamPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($creamSecret)
try { $creamToken = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($creamPointer) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($creamPointer) }
$creamHeaders = @{
    Authorization = 'Bearer ' + $creamToken
    Accept = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2026-03-10'
    'User-Agent' = 'CREAM-repository-setup'
}
$creamResults = [Collections.Generic.List[object]]::new()
function Invoke-CreamAdmin($Method, $Path, $Body = $null) {
    $creamRequest = @{ Method = $Method; Uri = "https://api.github.com/repos/$creamRepo/$Path"; Headers = $creamHeaders }
    if ($null -ne $Body) {
        $creamRequest.Body = ConvertTo-Json -InputObject $Body -Depth 20 -Compress
        $creamRequest.ContentType = 'application/json'
    }
    try {
        $value = Invoke-RestMethod @creamRequest
        $creamResults.Add([pscustomobject]@{ method=$Method; path=$Path; status='success' })
        return ,$value
    } catch {
        $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 'network error' }
        $creamResults.Add([pscustomobject]@{ method=$Method; path=$Path; status="HTTP $code" })
        return $null
    }
}
try {
    $creamMetadata = Invoke-CreamAdmin GET ''
    if (-not $creamMetadata -or -not $creamMetadata.permissions.admin) {
        throw 'The account/token must have repository administration access. No settings were changed.'
    }
    $null = Invoke-CreamAdmin PUT 'actions/permissions/workflow' @{
        default_workflow_permissions='read'; can_approve_pull_request_reviews=$false
    }
    $null = Invoke-CreamAdmin PUT 'actions/permissions' @{ enabled=$true; allowed_actions='selected' }
    $null = Invoke-CreamAdmin PUT 'actions/permissions/selected-actions' @{
        github_owned_allowed=$true; verified_allowed=$false; patterns_allowed=@()
    }
    $null = Invoke-CreamAdmin PUT 'actions/permissions/fork-pr-contributor-approval' @{
        approval_policy='all_external_contributors'
    }
    $null = Invoke-CreamAdmin PATCH '' @{ delete_branch_on_merge=$true }
    $null = Invoke-CreamAdmin PUT 'vulnerability-alerts'
    if (-not $creamMetadata.private) {
        $null = Invoke-CreamAdmin PUT 'private-vulnerability-reporting'
        $null = Invoke-CreamAdmin PATCH '' @{ security_and_analysis=@{
            secret_scanning=@{status='enabled'}; secret_scanning_push_protection=@{status='enabled'}
        }}
    } else {
        $creamResults.Add([pscustomobject]@{ method='SKIP'; path='public security features'; status='Repository remains private; rerun after publication' })
    }
    $creamRulesets = Invoke-CreamAdmin GET 'rulesets'
    $creamChecks = Invoke-CreamAdmin GET 'commits/main/check-runs'
    $creamCheck = $creamChecks.check_runs | Where-Object { $_.name -eq 'Test and package' -and $_.app.slug -eq 'github-actions' } | Select-Object -First 1
    if ($null -ne $creamRulesets -and $creamCheck) {
        $creamRuleset = @{
            name='CREAM main protection'; target='branch'; enforcement='active'; bypass_actors=@()
            conditions=@{ref_name=@{include=@('refs/heads/main'); exclude=@()}}
            rules=@(
                @{type='deletion'}, @{type='non_fast_forward'},
                @{type='pull_request'; parameters=@{
                    required_approving_review_count=0; dismiss_stale_reviews_on_push=$true
                    require_code_owner_review=$false; require_last_push_approval=$false
                    required_review_thread_resolution=$true
                }},
                @{type='required_status_checks'; parameters=@{
                    strict_required_status_checks_policy=$true
                    required_status_checks=@(@{context='Test and package'; integration_id=$creamCheck.app.id})
                }}
            )
        }
        $creamExisting = $creamRulesets | Where-Object { $_.name -eq 'CREAM main protection' } | Select-Object -First 1
        if ($creamExisting) { $null = Invoke-CreamAdmin PUT "rulesets/$($creamExisting.id)" $creamRuleset }
        else { $null = Invoke-CreamAdmin POST 'rulesets' $creamRuleset }
    } else {
        $creamResults.Add([pscustomobject]@{method='SKIP'; path='main ruleset'; status='Requires ruleset availability and a completed Test and package check'})
    }
    # Read back each category; never infer application merely from desired settings.
    foreach ($creamPath in @('actions/permissions/workflow','actions/permissions','actions/permissions/selected-actions',
                             'actions/permissions/fork-pr-contributor-approval','rulesets','private-vulnerability-reporting','')) {
        $creamValue = Invoke-CreamAdmin GET $creamPath
        if ($null -ne $creamValue) {
            Write-Host ("Verified response for /$creamPath")
            if ($creamPath -ne '') { $creamValue | ConvertTo-Json -Depth 10 | Write-Host }
            else { $creamValue | Select-Object full_name, visibility, delete_branch_on_merge, security_and_analysis | ConvertTo-Json -Depth 6 | Write-Host }
        }
    }
} finally {
    $creamHeaders.Remove('Authorization')
    $creamToken = $null
    $creamSecret.Dispose()
    $creamResults | Format-Table -AutoSize
}
