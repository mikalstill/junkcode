provider "azurerm" {
  version = "=1.38.0"
}

variable "location" {
  type = string
}

variable "resource_group" {
  type = string
}

data "azurerm_resource_group" "mikal_test_rg" {
  name = var.resource_group
}

variable "net" {
  type = string
}

data "azurerm_virtual_network" "mikal_test_net" {
  name                = var.net
  resource_group_name = "${data.azurerm_resource_group.mikal_test_rg.name}"
}

variable "subnet" {
  type = string
}

data "azurerm_subnet" "mikal_test_subnet" {
  name                 = var.subnet
  virtual_network_name = "${data.azurerm_virtual_network.mikal_test_net.name}"
  resource_group_name  = "${data.azurerm_resource_group.mikal_test_rg.name}"
}

resource "azurerm_network_interface" "mikal_test_nic" {
  name                = "mikal_test_nic"
  location            = "${data.azurerm_resource_group.mikal_test_rg.location}"
  resource_group_name = "${data.azurerm_resource_group.mikal_test_rg.name}"

  ip_configuration {
    name                          = "testconfiguration1"
    subnet_id                     = "${data.azurerm_subnet.mikal_test_subnet.id}"
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_virtual_machine" "mikal_test" {
  name                  = "mikal_test"
  location              = "${data.azurerm_resource_group.mikal_test_rg.location}"
  resource_group_name   = "${data.azurerm_resource_group.mikal_test_rg.name}"
  network_interface_ids = ["${azurerm_network_interface.mikal_test_nic.id}"]
  vm_size               = "Standard_B1ls"
  delete_os_disk_on_termination = true
  delete_data_disks_on_termination = true

  storage_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }
  storage_os_disk {
    name              = "mikal_test_os_disk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }
  os_profile {
    computer_name  = "hostname"
    admin_username = "testadmin"
    admin_password = "Password1234!"
  }
  os_profile_linux_config {
    disable_password_authentication = false
  }
}