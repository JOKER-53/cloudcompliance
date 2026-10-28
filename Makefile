.PHONY: start deploy deploy-prod validate test clean report drift history history-export remediate remediate-dry schedule destroy all serve

start:
	bash scripts/start.sh

test:
	python3 -m unittest discover tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.py[cod]" -delete 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/

deploy:
	cd terraform && terraform init && terraform apply -var-file=local.tfvars -auto-approve

deploy-prod:
	cd terraform && terraform init && terraform apply -var-file=prod.tfvars -auto-approve

validate:
	cd terraform && terraform validate && terraform fmt -check

report:
	cloudcompliance report

drift:
	cloudcompliance drift

history:
	cloudcompliance history

history-export:
	cloudcompliance history --export

remediate:
	cloudcompliance remediate

remediate-dry:
	cloudcompliance remediate --dry-run

schedule:
	cloudcompliance schedule --interval 60

destroy:
	cd terraform && terraform destroy -var-file=local.tfvars -auto-approve

all: deploy report drift history

serve:
	cloudcompliance serve
