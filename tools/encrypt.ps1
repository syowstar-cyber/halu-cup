# body.html を PBKDF2(SHA-256, 200000) → AES-256-CBC + HMAC-SHA256 で暗号化し cipher.json へ
$ErrorActionPreference = "Stop"
$here = Join-Path (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)) ".work"
$plain = [System.IO.File]::ReadAllBytes("$here\body.html")
$pw = ([System.IO.File]::ReadAllText("$here\pw.txt")).Trim()

$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$salt = New-Object byte[] 16; $rng.GetBytes($salt)
$iv   = New-Object byte[] 16; $rng.GetBytes($iv)

$kdf = New-Object System.Security.Cryptography.Rfc2898DeriveBytes($pw, $salt, 200000, [System.Security.Cryptography.HashAlgorithmName]::SHA256)
$keys = $kdf.GetBytes(64)
$aesKey = $keys[0..31]
$macKey = $keys[32..63]

$aes = [System.Security.Cryptography.Aes]::Create()
$aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
$aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
$aes.Key = $aesKey; $aes.IV = $iv
$enc = $aes.CreateEncryptor()
$ct = $enc.TransformFinalBlock($plain, 0, $plain.Length)

$hmac = New-Object System.Security.Cryptography.HMACSHA256(,$macKey)
$mac = $hmac.ComputeHash($iv + $ct)

$obj = @{
  salt = [Convert]::ToBase64String($salt)
  iv   = [Convert]::ToBase64String($iv)
  ct   = [Convert]::ToBase64String($ct)
  mac  = [Convert]::ToBase64String($mac)
  iter = 200000
}
$json = $obj | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText("$here\cipher.json", $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Output "OK $($ct.Length)"
