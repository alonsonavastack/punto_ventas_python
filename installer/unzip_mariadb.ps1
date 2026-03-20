param(
    [string]$ZipPath,
    [string]$DestPath
)

# Extraer ZIP a carpeta temporal
$tmpPath = "$DestPath`_tmp"
Expand-Archive -Force -LiteralPath $ZipPath -DestinationPath $tmpPath

# Detectar subcarpeta (ej: mariadb-12.2.2-winx64)
$subFolder = Get-ChildItem $tmpPath | Where-Object { $_.PSIsContainer } | Select-Object -First 1

if ($subFolder) {
    # Mover subcarpeta como destino final
    Move-Item -Path $subFolder.FullName -Destination $DestPath
    Remove-Item -Path $tmpPath -Recurse -Force
} else {
    # No hay subcarpeta, renombrar directamente
    Rename-Item -Path $tmpPath -NewName $DestPath
}

Write-Host "MariaDB extraido correctamente en: $DestPath"
exit 0
