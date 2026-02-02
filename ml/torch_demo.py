import torch
x = torch.ones(5)  # input tensor

print(x.shape)
print(x)
y = torch.zeros(3)  # expected output
w = torch.randn(5, 3, requires_grad=True)
print(w)
b = torch.randn(3, requires_grad=True)
z = torch.matmul(x, w)+b
loss = torch.nn.functional.binary_cross_entropy_with_logits(z, y)
import torch.nn as nn
nn.Linear()