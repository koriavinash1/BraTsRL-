import os
import random
import numpy as np
import cv2
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.backends.cudnn as cudnn
import torchvision.transforms as transforms
import torchvision
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from collections import OrderedDict

from torchvision.models.densenet import model_urls
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from torchvision.models.resnet import model_urls as resnetmodel_urls
from tqdm import tqdm

class DPGNetwork(nn.Module):
	"""
		
	"""
	def __init__(self, num_inputs = 1024, num_actions = 4, history_count = 4):
		super(DPGNetwork, self).__init__()
		# num_inputs = number of feature outputs + 4 past actions 24
		self.features     = nn.Sequential(OrderedDict([]))
		self.features.add_module('layer1', nn.ELU(nn.Linear(num_inputs + history_count*num_actions, 1024)))
		self.features.add_module('layer2', nn.ELU(nn.Linear(1024, 512)))
		self.features.add_module('layer3', nn.Linear(512, num_actions))
		self.features.add_module('tanh', nn.Tanh())

		# self.layer1 = nn.Linear(1048,1024)
		# self.layer2 = nn.Linear(1024, 512)
		# self.layer3 =nn.Linear(512, 6)

	def forward(self, state, past_actions):
		x = torch.cat([state.float(), past_actions.float()], 1)
		# actions= self.layer3(self.layer2(self.layer1(x)))
		actions = self.features(x)
		print (x)
		return actions


class featureExtractor(nn.Module):
	"""
		
	"""
	def __init__(self):
		super(featureExtractor, self).__init__()
		self.net = torchvision.models.densenet121(pretrained=True)
		self.net = nn.Sequential(*list(self.net.features.children())[:-3])
		self.net.add_module('adaptive', nn.AdaptiveAvgPool2d((1,1)))

	def forward(self, x):
		x = self.net(x)
		shape = x.size()[1]
		x = x.view(-1, shape)
		return x

class GLNFeatureExtractor(nn.Module):
	"""
		
	"""
	def __init__(self, isTrained = True, num_channel=1):
		super(GLNFeatureExtractor, self).__init__()
		model_urls['densenet121'] = model_urls['densenet121'].replace('https://', 'http://')
		self.first_conv  =nn.Sequential(nn.BatchNorm2d(num_channel),nn.Conv2d(num_channel, 3, kernel_size=3, padding=1))
		self.densenet121 = torchvision.models.densenet121(pretrained=isTrained)
		self.features    = self.densenet121.features

	def forward(self, x):
		x = self.first_conv(x)
		x = self.features(x)
		x = nn.functional.adaptive_avg_pool2d(x,(1,1)).view(x.size(0),-1)
		# x = self.classifier(x)
		return x

class combinedNetwork(nn.Module):
	"""
		combined net for 
	"""
	def __init__(self, ninputs=1024, nactions = 4, history_count = 4):
		super(combinedNetwork, self).__init__()
		self.features = GLNFeatureExtractor().cuda() # ? x 1024
		self.dpg     = DPGNetwork(num_inputs = ninputs, num_actions = nactions, history_count = history_count).cuda()

	def forward(self, x, history_vec):
		print (x.size(), history_vec.size())
		x = self.features(x)		
		x = self.dpg(x, history_vec)
		return x.view(-1, 2, 2)


if __name__ == "__main__":
	a   = torch.autograd.Variable(troch.rand(2, 9, 240, 240))
	h   = torch.autograd.Variable(torch.rand(2, 16))
	net = combinedNetwork()
	b   = net(a, h) 
	print (b.size())
