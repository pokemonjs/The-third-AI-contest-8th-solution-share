import paddle
import paddle.nn as nn

import paddle.nn.functional as F

class h_sigmoid(nn.Layer):
    def __init__(self, inplace=True):
        super(h_sigmoid, self).__init__()
        self.relu = nn.ReLU()

    def forward(self, x):
        return self.relu(x)

class h_swish(nn.Layer):
    def __init__(self, inplace=True):
        super(h_swish, self).__init__()
        self.sigmoid = h_sigmoid(inplace=inplace)

    def forward(self, x):
        return x * self.sigmoid(x)

class CoordAtt(nn.Layer):
    def __init__(self, inp, oup, reduction=16):
        super(CoordAtt, self).__init__()
        self.pool_h = nn.AdaptiveAvgPool2D((None, 1))
        self.pool_w = nn.AdaptiveAvgPool2D((1, None))

        mip = max(8, inp // reduction)

        self.conv1 = nn.Conv2D(inp, mip, kernel_size=1, stride=1, padding=0)
        self.bn1 = nn.BatchNorm2D(mip)
        self.act = h_swish()
        
        self.conv_h = nn.Conv2D(mip, oup, kernel_size=1, stride=1, padding=0)
        self.conv_w = nn.Conv2D(mip, oup, kernel_size=1, stride=1, padding=0)
        

    def forward(self, x):
        identity = x
        
        #n,c,h,w = x.size()
        n,c,h,w = x.shape
        x_h = self.pool_h(x)
        x_w = self.pool_w(x)
        x_w = paddle.transpose(x_w, [0, 1, 3, 2])

        y = paddle.concat([x_h, x_w], axis = 2)
        y = self.conv1(y)
        y = self.bn1(y)
        y = self.act(y) 
        
        x_h, x_w = paddle.split(y, [h, w], axis=2)
        # x_w = x_w.permute(0, 1, 3, 2)
        x_w = paddle.transpose(x_w,[0,1,3,2])
        a_h = self.conv_h(x_h)
        a_h = F.sigmoid(a_h)
        a_w = self.conv_w(x_w)
        a_w = F.sigmoid(a_w)

        out = identity * a_w * a_h

        return out
