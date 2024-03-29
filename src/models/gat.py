import torch
from torch import Tensor
from torch.nn import Parameter, Linear
from torch.nn import functional as F
from typing import Union, Tuple, Optional
from torch_geometric.typing import Size,OptTensor,Adj,OptPairTensor
from torch_geometric.nn import global_add_pool, global_mean_pool, MessagePassing, GATConv
from torch_sparse import SparseTensor, matmul, fill_diag, sum as sparsesum, mul
from torch_geometric.nn.inits import glorot, zeros
from torch_geometric.utils import softmax
from torch import nn
import torch_geometric
import json

class MPGATConv(GATConv):
    def __init__(self, in_channels, out_channels, heads, concat: bool = True,
                 negative_slope: float = 0.2, dropout: float = 0.0, bias: bool = True, gat_mp_type: str="attention_weighted"):
        super().__init__(in_channels, out_channels, heads)
        print(f'In Chan {in_channels}')
        print(f'Out Chan {out_channels}')
        print(f'Heads {heads}')

        self.gat_mp_type = gat_mp_type
        
    def forward(self, x: Union[Tensor, OptPairTensor], edge_index: Adj,
                edge_attr: OptTensor = None, size: Size = None,
                return_attention_weights=None):
        # Call the superclass's forward method
        x, (edge_ind, alpha) = super().forward(x, edge_index,edge_attr=edge_attr, size=size, return_attention_weights=True)
        # Store the attention weights
    
        # Write the attention weights to a file
        torch.save(edge_ind,'edge_indicies.pt')
        torch.save(alpha, 'attention_weights.pt')
        
        return x
        
    # def message(self, x_j: Tensor, alpha: Tensor, edge_attr: OptTensor) -> Tensor:
    #     if edge_attr is not None:
    #         print(f"Edge attributes exist with shape: {edge_attr.shape} and type: {edge_attr.dtype}")
    #     else:
    #         print("Edge attributes are None")
    #     edge_weights = torch.abs(edge_attr.view(-1, 1).unsqueeze(-1))

    #     if self.gat_mp_type == "attention_weighted":
    #         msg = x_j * alpha.unsqueeze(-1)
    #     elif self.gat_mp_type == "attention_edge_weighted":
    #         if edge_weights is None:
    #             raise ValueError("Edge attributes are required for 'attention_edge_weighted' message passing.")
    #         msg = x_j * alpha.unsqueeze(-1) * edge_weights
    #     elif self.gat_mp_type == "sum_attention_edge":
    #         if edge_weights is None:
    #             raise ValueError("Edge attributes are required for 'sum_attention_edge' message passing.")
    #         msg = x_j * (alpha.unsqueeze(-1) + edge_weights)

    #     else:
    #         raise ValueError(f"Invalid message passing variant: {self.gat_mp_type}")

    #     return msg
 
     

    # def message(self, x_i, x_j, alpha_j, alpha_i, edge_attr, index, ptr, size_i):
    #     print(f'Message type {self.gat_mp_type}')
    #     print(f'x_j {x_j}')
    #     print(f'x_i {x_i}')
 
    #     alpha = alpha_j if alpha_i is None else alpha_j + alpha_i
    #     alpha = F.leaky_relu(alpha, self.negative_slope)
    #     alpha = softmax(alpha, index, ptr, size_i)
    #     self._alpha = alpha
    #     alpha = F.dropout(alpha, p=self.dropout, training=self.training)

    #     attention_score = alpha.unsqueeze(-1)  
    #     edge_weights = torch.abs(edge_attr.view(-1, 1).unsqueeze(-1))

    #     if self.gat_mp_type == "attention_weighted":
    #         # (1) att: s^(l+1) = s^l * alpha
    #         msg = x_j * attention_score
    #         return msg
    #     elif self.gat_mp_type == "attention_edge_weighted":
    #         # (2) e-att: s^(l+1) = s^l * alpha * e
    #         msg = x_j * attention_score * edge_weights
    #         return msg
    #     elif self.gat_mp_type == "sum_attention_edge":
    #         # (3) m-att-1: s^(l+1) = s^l * (alpha + e), this one may not make sense cause it doesn't used attention score to control all
    #         msg = x_j * (attention_score + edge_weights)
    #         return msg
    #     elif self.gat_mp_type == "edge_node_concate":
    #         # (4) m-att-2: s^(l+1) = linear(concat(s^l, e) * alpha)
    #         msg = torch.cat([x_i, x_j * attention_score, edge_attr.view(-1, 1).unsqueeze(-1).expand(-1, self.heads, -1)], dim=-1)
    #         msg = self.edge_lin(msg)
    #         return msg
    #     elif self.gat_mp_type == "node_concate":
    #         # (4) m-att-2: s^(l+1) = linear(concat(s^l, e) * alpha)
    #         msg = torch.cat([x_i, x_j * attention_score], dim=-1)
    #         msg = self.edge_lin(msg)
    #         return msg
    #     # elif self.gat_mp_type == "sum_node_edge_weighted":
    #     #     # (5) m-att-3: s^(l+1) = (s^l + e) * alpha
    #     #     node_emb_dim = x_j.shape[-1]
    #     #     extended_edge = torch.cat([edge_weights] * node_emb_dim, dim=-1)
    #     #     sum_node_edge = x_j + extended_edge
    #     #     msg = sum_node_edge * attention_score
    #     #     return msg
    #     else:
    #         raise ValueError(f'Invalid message passing variant {self.gat_mp_type}')


class GAT(torch.nn.Module):
    def __init__(self, input_dim, args, num_nodes, num_classes):
        super().__init__()
        self.activation = torch.nn.ReLU()
        self.convs = torch.nn.ModuleList()
        self.pooling = args.pooling
        self.num_nodes = num_nodes

        hidden_dim = args.hidden_dim
        num_heads = args.num_heads
        num_layers = args.n_GNN_layers
        edge_emb_dim = args.edge_emb_dim
        gat_mp_type = args.gat_mp_type
        dropout = args.dropout

        gat_input_dim = input_dim

        for i in range(num_layers-1):
            # print(f'Gat input dim  {gat_input_dim}')
            # print(f'Gat hidden dim  {hidden_dim}')
            # print(f'Gat num heads  {num_heads}')
            # print(f'Gat dropout  {dropout}')
            # print(f'Gat mp type  {gat_mp_type}')
            
            conv = torch_geometric.nn.Sequential('x, edge_index, edge_attr', [
                (MPGATConv(gat_input_dim, hidden_dim, heads=num_heads, dropout=dropout,
                                 gat_mp_type=gat_mp_type),'x, edge_index, edge_attr -> x'),
                nn.Linear(hidden_dim*num_heads, hidden_dim),
                nn.LeakyReLU(negative_slope=0.2),
                nn.BatchNorm1d(hidden_dim)
            ])
            gat_input_dim = hidden_dim
            self.convs.append(conv)
            # print("finished")

        input_dim = 0

        if self.pooling == "concat":
            # print("WE concatting")
            node_dim = 8
            conv = torch_geometric.nn.Sequential('x, edge_index, edge_attr', [
                (MPGATConv(hidden_dim, hidden_dim, heads=num_heads, dropout=dropout,
                                 gat_mp_type=gat_mp_type),'x, edge_index, edge_attr -> x'),
                nn.Linear(hidden_dim*num_heads, 64),
                nn.LeakyReLU(negative_slope=0.2),
                nn.Linear(64, node_dim),
                nn.LeakyReLU(negative_slope=0.2),
                nn.BatchNorm1d(node_dim)
            ])
            input_dim = node_dim*num_nodes
            print("Finished concatting")

        elif self.pooling == 'sum' or self.pooling == 'mean':
            node_dim = 256
            input_dim = node_dim
            conv = torch_geometric.nn.Sequential('x, edge_index, edge_attr', [
                (MPGATConv(hidden_dim, hidden_dim, heads=num_heads, dropout=dropout,
                                 gat_mp_type=gat_mp_type),'x, edge_index, edge_attr -> x'),
                nn.Linear(hidden_dim* num_heads, hidden_dim),
                nn.LeakyReLU(negative_slope=0.2),
                nn.BatchNorm1d(node_dim)
            ])

        self.convs.append(conv)

        self.fcn = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.LeakyReLU(negative_slope=0.2),
            nn.Linear(256, 32),
            nn.LeakyReLU(negative_slope=0.2),
            nn.Linear(32, 2)
        )
        print(self.convs)

    def forward(self, x, edge_index, edge_attr, batch):
        z = x
        edge_attr = torch.abs(edge_attr)
   
        for i, conv in enumerate(self.convs):
            # bz*nodes, hidden
            # print(f'Conv {i} input {z.shape}, edge_index {edge_index.shape}, edge_attr {edge_attr.shape}')
            z = conv(z, edge_index, edge_attr)


        if self.pooling == "concat":
            z = z.reshape((z.shape[0]//self.num_nodes, -1))
        elif self.pooling == 'sum':
            z = global_add_pool(z,  batch)  # [N, F]
        elif self.pooling == 'mean':
            z = global_mean_pool(z, batch)  # [N, F]

        out = self.fcn(z)
        return out

        