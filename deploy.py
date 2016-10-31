import subprocess
import os
import sys
from datetime import datetime

class Terraform:
    """Class to perfor the Terraform Operations"""
    def __init__(self, terraform_dir, variables=None):
        """Generate the absoluet path for terraform directory"""
        self.terraform_dir = os.path.join(os.getcwd(),terraform_dir)
        


    def parse_output(self,process):
        """Print the output in console"""
        for line in iter(process.stdout.readline, b''):
            print line


    def apply(self):
        """Terraform Apply the plan to get real resources"""
        cmd = "terraform apply  -var-file=~/.aws/credentials" + " " + self.terraform_dir
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1,universal_newlines = True,shell=True)
        output = self.parse_output(p)
        p.stdout.close()
        

    def get(self):
        """Load the Terraform Modules"""
        cmd = "terraform get " + self.terraform_dir
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1,universal_newlines = True,shell=True)
        output = self.parse_output(p)
        p.stdout.close()
        
    def destroy(self):
        """Destroy the infra structure"""
        cmd = "terraform destroy -input=false -force -var-file=~/.aws/credentials " + self.terraform_dir
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, shell=True)
        output = self.parse_output(p)
        p.stdout.close()
        return output
        

tf = Terraform("terraform")
func = getattr(tf, sys.argv[1])
func()

