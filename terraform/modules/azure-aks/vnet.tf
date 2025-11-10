# Azure Virtual Network Configuration for AKS
# Swiss Engineering Standards: Secure, Efficient Network Architecture

# Local values for network configuration
locals {
  create_resource_group = var.resource_group_name == ""
  create_vnet          = var.vnet_name == ""
  create_subnet        = var.subnet_name == ""
  vnet_name            = local.create_vnet ? "${local.cluster_name}-vnet" : var.vnet_name
  subnet_name          = local.create_subnet ? "${local.cluster_name}-subnet" : var.subnet_name
}

# Data sources for existing resources (if provided)
data "azurerm_resource_group" "existing" {
  count = local.create_resource_group ? 0 : 1
  name  = var.resource_group_name
}

data "azurerm_virtual_network" "existing" {
  count               = local.create_vnet ? 0 : 1
  name                = var.vnet_name
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
}

data "azurerm_subnet" "existing" {
  count                = local.create_subnet ? 0 : 1
  name                 = var.subnet_name
  virtual_network_name = local.vnet_name
  resource_group_name  = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
}

# Resource Group (created if resource_group_name is empty)
resource "azurerm_resource_group" "main" {
  count = local.create_resource_group ? 1 : 0

  name     = local.resource_group_name
  location = var.location

  tags = merge(local.common_tags, {
    Component = "resource-management"
    Purpose   = "aks-cluster"
  })
}

# Virtual Network (created if vnet_name is empty)
resource "azurerm_virtual_network" "main" {
  count = local.create_vnet ? 1 : 0

  name                = local.vnet_name
  address_space       = var.vnet_address_space
  location            = var.location
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name

  # DNS servers for Swiss compliance (if required)
  dns_servers = var.swiss_compliance_enabled && var.security_level == "maximum" ? [
    "168.63.129.16", # Azure default DNS
    "8.8.8.8",       # Google DNS backup
  ] : null

  tags = merge(local.common_tags, {
    Component = "networking"
    Purpose   = "aks-cluster"
  })
}

# Subnet for AKS cluster (created if subnet_name is empty)
resource "azurerm_subnet" "aks" {
  count = local.create_subnet ? 1 : 0

  name                 = local.subnet_name
  resource_group_name  = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
  virtual_network_name = local.create_vnet ? azurerm_virtual_network.main[0].name : data.azurerm_virtual_network.existing[0].name
  address_prefixes     = [var.subnet_address_prefix]

  # Service endpoints for enhanced security
  service_endpoints = var.security_level != "basic" ? [
    "Microsoft.ContainerRegistry",
    "Microsoft.KeyVault",
    "Microsoft.Storage",
    "Microsoft.Sql"
  ] : []

  # Delegation for Azure CNI (if enabled)
  dynamic "delegation" {
    for_each = var.enable_azure_cni ? [1] : []
    content {
      name = "aks-delegation"
      service_delegation {
        name    = "Microsoft.ContainerService/managedClusters"
        actions = [
          "Microsoft.Network/virtualNetworks/subnets/join/action",
        ]
      }
    }
  }
}

# Dedicated subnet for pods (Azure CNI with dynamic IP allocation)
resource "azurerm_subnet" "pods" {
  count = local.create_subnet && var.enable_azure_cni && var.pod_subnet_address_prefix != "" ? 1 : 0

  name                 = "${local.subnet_name}-pods"
  resource_group_name  = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
  virtual_network_name = local.create_vnet ? azurerm_virtual_network.main[0].name : data.azurerm_virtual_network.existing[0].name
  address_prefixes     = [var.pod_subnet_address_prefix]

  delegation {
    name = "aks-pod-delegation"
    service_delegation {
      name    = "Microsoft.ContainerService/managedClusters"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

# Network Security Group for AKS subnet (enhanced security)
resource "azurerm_network_security_group" "aks" {
  count = var.security_level != "basic" && local.create_subnet ? 1 : 0

  name                = "${local.cluster_name}-nsg"
  location            = var.location
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name

  # Allow inbound traffic for Kubernetes API server
  security_rule {
    name                       = "AllowKubernetesAPI"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "Internet"
    destination_address_prefix = "*"
  }

  # Allow inbound traffic for NodePort services
  security_rule {
    name                       = "AllowNodePorts"
    priority                   = 1100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "30000-32767"
    source_address_prefix      = "Internet"
    destination_address_prefix = "*"
  }

  # Allow HTTP and HTTPS for Epic 8 services
  security_rule {
    name                       = "AllowHTTPHTTPS"
    priority                   = 1200
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["80", "443"]
    source_address_prefix      = "Internet"
    destination_address_prefix = "*"
  }

  # Allow Epic 8 service communication
  security_rule {
    name                       = "AllowEpic8Services"
    priority                   = 1300
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["8080", "8081", "8082", "8083", "8084", "8085"]
    source_address_prefix      = var.subnet_address_prefix
    destination_address_prefix = var.subnet_address_prefix
  }

  # Allow monitoring and metrics
  security_rule {
    name                       = "AllowMonitoring"
    priority                   = 1400
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["9090", "9091", "9092", "9093", "9094", "9095"]
    source_address_prefix      = var.subnet_address_prefix
    destination_address_prefix = var.subnet_address_prefix
  }

  # Allow Redis cache
  security_rule {
    name                       = "AllowRedis"
    priority                   = 1500
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "6379"
    source_address_prefix      = var.subnet_address_prefix
    destination_address_prefix = var.subnet_address_prefix
  }

  # Deny all other inbound traffic (maximum security)
  dynamic "security_rule" {
    for_each = var.security_level == "maximum" ? [1] : []
    content {
      name                       = "DenyAllInbound"
      priority                   = 4000
      direction                  = "Inbound"
      access                     = "Deny"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "*"
      source_address_prefix      = "*"
      destination_address_prefix = "*"
    }
  }

  # Allow all outbound traffic
  security_rule {
    name                       = "AllowAllOutbound"
    priority                   = 1000
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = merge(local.common_tags, {
    Component = "security"
    Purpose   = "network-security"
  })
}

# Associate NSG with AKS subnet
resource "azurerm_subnet_network_security_group_association" "aks" {
  count = var.security_level != "basic" && local.create_subnet ? 1 : 0

  subnet_id                 = azurerm_subnet.aks[0].id
  network_security_group_id = azurerm_network_security_group.aks[0].id
}

# Route Table for custom routing (maximum security)
resource "azurerm_route_table" "aks" {
  count = var.security_level == "maximum" && local.create_subnet ? 1 : 0

  name                          = "${local.cluster_name}-rt"
  location                      = var.location
  resource_group_name           = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
  disable_bgp_route_propagation = false

  # Custom route for Epic 8 traffic
  route {
    name                   = "Epic8InternalTraffic"
    address_prefix         = var.service_cidr
    next_hop_type          = "VnetLocal"
    next_hop_in_ip_address = null
  }

  # Route to Azure services through service endpoints
  route {
    name           = "AzureServices"
    address_prefix = "0.0.0.0/0"
    next_hop_type  = "Internet"
  }

  tags = merge(local.common_tags, {
    Component = "networking"
    Purpose   = "custom-routing"
  })
}

# Associate Route Table with AKS subnet
resource "azurerm_subnet_route_table_association" "aks" {
  count = var.security_level == "maximum" && local.create_subnet ? 1 : 0

  subnet_id      = azurerm_subnet.aks[0].id
  route_table_id = azurerm_route_table.aks[0].id
}

# NAT Gateway for outbound internet access (enhanced security)
resource "azurerm_public_ip" "nat_gateway" {
  count = var.security_level != "basic" && local.create_subnet ? 1 : 0

  name                = "${local.cluster_name}-nat-gateway-pip"
  location            = var.location
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = local.current_config.availability_zones

  tags = merge(local.common_tags, {
    Component = "networking"
    Purpose   = "nat-gateway"
  })
}

resource "azurerm_nat_gateway" "main" {
  count = var.security_level != "basic" && local.create_subnet ? 1 : 0

  name                    = "${local.cluster_name}-nat-gateway"
  location                = var.location
  resource_group_name     = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
  sku_name                = "Standard"
  idle_timeout_in_minutes = 10
  zones                   = local.current_config.availability_zones

  tags = merge(local.common_tags, {
    Component = "networking"
    Purpose   = "outbound-connectivity"
  })
}

resource "azurerm_nat_gateway_public_ip_association" "main" {
  count = var.security_level != "basic" && local.create_subnet ? 1 : 0

  nat_gateway_id       = azurerm_nat_gateway.main[0].id
  public_ip_address_id = azurerm_public_ip.nat_gateway[0].id
}

resource "azurerm_subnet_nat_gateway_association" "main" {
  count = var.security_level != "basic" && local.create_subnet ? 1 : 0

  subnet_id      = azurerm_subnet.aks[0].id
  nat_gateway_id = azurerm_nat_gateway.main[0].id
}

# VNet Peering for multi-region setup (production environments)
resource "azurerm_virtual_network_peering" "epic8_peering" {
  count = var.environment == "prod" && var.swiss_compliance_enabled && local.create_vnet ? 1 : 0

  name                      = "${local.cluster_name}-peering"
  resource_group_name       = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
  virtual_network_name      = azurerm_virtual_network.main[0].name
  remote_virtual_network_id = azurerm_virtual_network.main[0].id  # Placeholder - would be actual remote VNet

  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  allow_gateway_transit        = false
  use_remote_gateways         = false

  depends_on = [azurerm_virtual_network.main]
}

# Private DNS Zone for private cluster (if enabled)
resource "azurerm_private_dns_zone" "aks" {
  count = var.enable_private_cluster && var.private_dns_zone_id == "System" ? 1 : 0

  name                = "${local.cluster_name}.privatelink.${var.location}.azmk8s.io"
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name

  tags = merge(local.common_tags, {
    Component = "networking"
    Purpose   = "private-dns"
  })
}

resource "azurerm_private_dns_zone_virtual_network_link" "aks" {
  count = var.enable_private_cluster && var.private_dns_zone_id == "System" && local.create_vnet ? 1 : 0

  name                  = "${local.cluster_name}-dns-link"
  resource_group_name   = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
  private_dns_zone_name = azurerm_private_dns_zone.aks[0].name
  virtual_network_id    = azurerm_virtual_network.main[0].id

  tags = merge(local.common_tags, {
    Component = "networking"
    Purpose   = "private-dns-link"
  })
}

# Application Security Groups for Epic 8 services
resource "azurerm_application_security_group" "epic8_api" {
  count = var.security_level == "maximum" ? 1 : 0

  name                = "${local.cluster_name}-epic8-api-asg"
  location            = var.location
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name

  tags = merge(local.common_tags, {
    Component = "security"
    Purpose   = "api-services"
    Platform  = "epic8-rag"
  })
}

resource "azurerm_application_security_group" "epic8_ml" {
  count = var.security_level == "maximum" ? 1 : 0

  name                = "${local.cluster_name}-epic8-ml-asg"
  location            = var.location
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name

  tags = merge(local.common_tags, {
    Component = "security"
    Purpose   = "ml-services"
    Platform  = "epic8-rag"
  })
}

resource "azurerm_application_security_group" "epic8_data" {
  count = var.security_level == "maximum" ? 1 : 0

  name                = "${local.cluster_name}-epic8-data-asg"
  location            = var.location
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name

  tags = merge(local.common_tags, {
    Component = "security"
    Purpose   = "data-services"
    Platform  = "epic8-rag"
  })
}