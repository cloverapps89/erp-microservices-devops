Write-Host "=== DevOps Toolbox Setup Script ===" -ForegroundColor Cyan

# Function to install or upgrade a tool based on version
function Ensure-Tool($name, $checkCmd, $chocoPkg, $emoji, $minimumVersion, $versionCmd) {
    Write-Host "`nChecking 📦 $name..."

    $installed = Get-Command $checkCmd -ErrorAction SilentlyContinue
    if ($installed) {
        $versionOutput = & $versionCmd
		$firstLine = $versionOutput | Select-Object -First 1
		Write-Host "$versionOutput"
        if ($firstLine -match "v?(\d+\.\d+\.\d+)") {
            $currentVersion = $Matches[1]
            if ($currentVersion -lt $minimumVersion) {
                Write-Host "$emoji $name version $currentVersion is outdated. Upgrading to $minimumVersion..." -ForegroundColor Yellow
                choco upgrade $chocoPkg -y
            } else {
                Write-Host "$emoji $name is up-to-date ✅ ($currentVersion)" -ForegroundColor Green
            }
        } else {
            Write-Host "$emoji Unable to parse version for $name. Skipping version check." -ForegroundColor Red
        }
    } else {
        Write-Host "$emoji $name not found. Installing..." -ForegroundColor Yellow
        choco install $chocoPkg -y
    }
}

# Ensure Chocolatey is installed first
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "🍫 Chocolatey not found. Installing..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
} else {
    Write-Host "🍫 Chocolatey already installed ✅" -ForegroundColor Green
}

# 1. Git
Ensure-Tool "Git" "git" "git" "🧬" "2.51.0" { git --version }

# 2. Terraform
Ensure-Tool "Terraform" "terraform" "terraform" "🌍" "1.13.1" { terraform --version }

# 3. Docker Desktop (manual install for Windows)
Write-Host "`nChecking Docker..."
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker --version
    try {
        docker run --rm hello-world > $null
		cd .\erp-microservices-devops
		docker compose up --build test-runner
		docker compose down 
        Write-Host "🐳 Docker is working ✅" -ForegroundColor Green
    } catch {
        Write-Host "Docker installed but test failed. Make sure Docker Desktop is running." -ForegroundColor Yellow
    }
} else {
    Write-Host "Docker Desktop must be installed..." -ForegroundColor Red
    choco install docker-desktop -y
    docker --version
    Write-Host "🐳 Docker Desktop installed..."
    try {
        docker run --rm hello-world > $null
        Write-Host "🐳 Docker is working ✅" -ForegroundColor Green
    } catch {
        Write-Host "Docker installed but test failed. Make sure Docker Desktop is running." -ForegroundColor Yellow
    }
}

# 4. Minikube & kubectl
Ensure-Tool "Minikube" "minikube" "minikube" "🧭" "1.32.0" { minikube version --short }
Ensure-Tool "kubectl" "kubectl" "kubernetes-cli" "🧭" "1.32.0" { kubectl version --client }

# Minikube health check
try {
    $minikubeStatus = minikube status 2>&1
    if ($minikubeStatus -match "Running" -and $minikubeStatus -notmatch "Stopped|Error|unknown state") {
        Write-Host "🧭 Minikube cluster is running ✅" -ForegroundColor Green
		minikube status
		minikube profile list
    } else {
        Write-Host "🧭 Minikube is not healthy. Starting cluster..." -ForegroundColor Yellow
		minikube status
		minikube profile list
        minikube delete
        minikube start --driver=docker
        kubectl get nodes
    }
} catch {
    Write-Host "🧭 Minikube status check failed. Starting fresh..." -ForegroundColor Yellow
    minikube delete
    minikube start --driver=docker
    kubectl get nodes
}


# 5. AWS CLI (optional block)
<# Ensure-Tool "AWS CLI" "aws" "awscli" "☁️" "2.15.0" { aws --version }
aws sts get-caller-identity | Out-Null
Write-Host "☁️ AWS CLI configured ✅" -ForegroundColor Green #>

Write-Host "`n=== Setup Complete! Your DevOps toolbox is ready 🚀 ===" -ForegroundColor Cyan
