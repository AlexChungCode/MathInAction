import torch
from src.models import GAT, GCN, BrainNN, MLP
from torch_geometric.data import Data
from typing import List


def build_model(args, device, model_name, num_features, num_nodes):
    # print(f'gcn with args {args}, num of nodes {num_nodes}, num features {num_features}')
    if model_name == 'gcn':
        model = BrainNN(args,
                      GCN(num_features, args, num_nodes, num_classes=2),
                      MLP(2 * num_nodes, args.hidden_dim, args.n_MLP_layers, torch.nn.ReLU, n_classes=2),
                      ).to(device)
    elif model_name == 'gat':
        # print(f'gat with args {args}, num of nodes {num_nodes}, num features {num_features}')
        model = BrainNN(args,
                      GAT(num_features, args, num_nodes, num_classes=2),
                      MLP(2 * num_nodes, args.gat_hidden_dim, args.n_MLP_layers, torch.nn.ReLU, n_classes=2),
                      ).to(device)
        
    elif model_name == 'gat_hir':
        print("Not yet implemented")
        raise NotImplementedError
    else:
        raise ValueError(f"ERROR: Model variant \"{args.variant}\" not found!")
    return model
