provider "azurerm" {
  version = "=1.38.0"
}

variable "location" {
  type = string
}

resource "azurerm_resource_group" "mikal_test_rg" {
  name     = "mikal_test_rg"
  location = var.location
}

resource "azurerm_virtual_network" "mikal_test_net" {
  name                = "mikal_test_net"
  resource_group_name = "${azurerm_resource_group.mikal_test_rg.name}"
  location            = "${azurerm_resource_group.mikal_test_rg.location}"
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "mikal_test_subnet" {
  name                 = "mikal_test_subnet"
  resource_group_name  = "${azurerm_resource_group.mikal_test_rg.name}"
  virtual_network_name = "${azurerm_virtual_network.mikal_test_net.name}"
  address_prefix       = "10.0.2.0/24"
}