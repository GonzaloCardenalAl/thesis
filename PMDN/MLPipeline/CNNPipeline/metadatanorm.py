import torch
import torch.nn as nn
import torch.nn.functional as F

class MetadataNorm(nn.Module):
    def __init__(self, batch_size, cf_kernel, dataset_size, num_features, momentum=0.1): 
        """ Metadata Normalization (MDN) module. MDN can be applied to layers in a neural network as a 
        normalization technique to remove metadata effects from the features in a network at the batch level.
        self.cfs must be set for every new batch based on the confounders for the batch. 
.
        Args:
          batch_size (int): batch size
          cf_kernel (2d vector): precalculated kernel for MDN based on the vector X of confounders (X^TX)^-1
          dataset_size (int): size of dataset
          num_features (int): number of features used to initialize beta
          momentum (float): momentum for stored beta
        """
        super(MetadataNorm, self).__init__()
        self.cf_kernel = cf_kernel
        self.batch_size = batch_size
        self.kernel_dim = cf_kernel.shape[0]
        self.cfs = nn.Parameter(torch.randn(batch_size, self.kernel_dim), requires_grad=False)
        self.dataset_size = dataset_size
        self.num_features = num_features
        self.register_buffer('beta', torch.zeros(self.kernel_dim, self.num_features))
        self.momentum = momentum # If momentum is None, standard average is used
        if momentum == None:
            self.momentum = 0.5
        
    def forward(self, x):
        Y = x
        N = x.shape[0]
        Y = Y.reshape(N, -1)
        X_batch = self.cfs # confounders for this batch only
        scale = self.dataset_size / self.batch_size
        if self.training:
            XT = torch.transpose(X_batch, 0, 1)
            pinv = torch.mm(self.cf_kernel, XT) 
            B = torch.mm(pinv, Y)
            with torch.no_grad():
                self.beta = (1 - self.momentum) * self.beta + self.momentum * B     
        else:
            B = self.beta
            
        #print("Beta", self.beta)
        #print("Summed Beta", torch.sum(self.beta))
         
        Y_r = torch.mm(X_batch[:, 1:], B[1:]) 
        residual = Y - scale * Y_r
        residual = residual.reshape(x.shape)
        return residual
