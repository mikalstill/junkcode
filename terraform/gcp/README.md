This is a worked example of how to start a Google cloud instance with
pre-configured ssh authentication. It assumes that you're keen for the
ssh user to be named "mikalstill" and have the ssh key that I use.
Perhaps that's not right for you?

To use:

```bash
$ terraform plan -var-file=demo.tfvars 
$ terraform apply -var-file=demo.tfvars
[...snip...]
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

instance_ip_addr = 35.223.232.207
$ ssh -i ~/.ssh/id_gcp_mikalstill mikalstill@35.223.232.207
```