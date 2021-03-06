# -*- coding: utf-8 -*-
"""problem2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iCSjS8c7zoLbDWCiuFR8Vej4OFvcipIC

report: 
The successful rate for all four model is 100%. Given a target, we can always get desire result in certain iterations. You can change your target picture freely. Time cost and number of iteration may vary for different target. eps I choose is 0.03 which according to my test works for all models. If eps is too large, attack resnet-18 will become inconsistent. The size of the target image could not smaller than 256*256.
"""

import torch
import torch.nn
import time
#from torch.autograd.gradcheck import zero_gradients
import torch.nn.functional as F
import torchvision.models as models
from PIL import Image
from torchvision import transforms
import numpy as np
import requests, io
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from torch.autograd import Variable
!pip3 install foolbox==3.1.1
import foolbox as fb
#import linalg to calculate p-norm
from numpy import linalg as LA
import eagerpy as ep

def zero_gradients(i):
    for t in iter_gradients(i):
        t.zero_()

"""comment the model that you are not currently testing

##choose a model
"""

#model = torch.hub.load('pytorch/vision:v0.6.0', 'resnet18', pretrained=True)
#model = torch.hub.load('pytorch/vision:v0.6.0', 'mobilenet_v2', pretrained=True)
#model = torch.hub.load('pytorch/vision:v0.6.0', 'vgg19', pretrained=True)
model = torch.hub.load('pytorch/vision:v0.6.0', 'alexnet', pretrained=True)
model.eval()

"""##choose image"""

# you can choose whatever image you like. I choose image from google image as my target.
import urllib
url, filename = ("http://www.krugerpark.co.za/images/black-maned-lion-shem-compion-590x390.jpg", "lion.jpg")
urllib.request.urlretrieve(url, filename)
input_image = Image.open(filename)
plt.imshow(input_image)

"""## preprocess"""

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
input_tensor = preprocess(input_image)
input_batch = input_tensor.unsqueeze(0)

original = input_batch

"""after preprocess, image will looks like this. """

plt.imshow(input_batch.cpu().detach().numpy()[0][0])

input_batch=input_batch.to('cuda') #comment this line out if CPU only
input_batch.requires_grad=True
model.to('cuda') #comment this line out if CPU only
output = model(input_batch)
# The output has unnormalized scores. To get probabilities, you can run a softmax on it.
probabilities = torch.nn.functional.softmax(output[0], dim=0)

"""import categories list'imagenet_classes.txt' from github. You can import the file to your google drive."""

from google.colab import drive
with open("/content/drive/MyDrive/imagenet_classes.txt", "r") as f: # you can download from https://github.com/Yifei-Li1/imagenet_classes/blob/main/imagenet_classes.txt
    categories = [s.strip() for s in f.readlines()]

"""first prediction"""

# Show top categories per image
top5_prob, top5_catid = torch.topk(probabilities, 5)
for i in range(top5_prob.size(0)):
    print(categories[top5_catid[i]], top5_prob[i].item())

print('----------------------------------------------------')

def plot_img(input_image):
    """
    x is a BGR image with shape (? ,224, 224, 3) 
    """
    t = np.zeros_like(input_image[0])
    t[:,:,0] = input_image[0][:,:,2]
    t[:,:,1] = input_image[0][:,:,1]
    t[:,:,2] = input_image[0][:,:,0]  
    plt.imshow(np.clip((t+[123.68, 116.779, 103.939]), 0, 255)/255)
    plt.grid('off')
    plt.axis('off')
    plt.show(input_image)

"""The attack, I let the iteration stop whenever the most posible prediction is our desired target."""

start_time = time.time()
for i in range(500):
  output = model(input_batch)
  print('----------------------------------------------------')
  y = 943   #cucumber, or change to whatever you like  
  target = Variable(torch.LongTensor([y]), requires_grad=False)
  target=target.to('cuda') #comment this line out if CPU only
  loss = torch.nn.CrossEntropyLoss()
  loss_cal = loss(output, target)
  loss_cal.backward(retain_graph=True)
  eps = 0.03 # works for every model
  x_grad = torch.sign(input_batch.grad.data)                #calculate the sign of gradient of the loss func (with respect to input X) (adv)
  input_batch.data = input_batch.data - eps * x_grad          #find adv example using formula shown above
  output_adv = model.forward(Variable(input_batch.data))   #perform a forward pass on adv example
  
  op_adv_probs = F.softmax(output_adv[0], dim=0)                 #get probability distribution over classes
  top5_prob, top5_catid = torch.topk(op_adv_probs, 5)

  for j in range(top5_prob.size(0)):
      print(i, categories[top5_catid[j]], top5_prob[j].item())
  if(categories[top5_catid[0]] == categories[y]):       #you can comment this if you want to increase the prediction result.
    break             #you can comment this if you want to further increase the prediction result.
timeCost = [time.time() - start_time]   #get the time cost of the attack
print("Time cost: ")
print(timeCost)

"""result image after attack"""

plt.imshow(input_batch.cpu().detach().numpy()[0][0])

p_norm = []
#L0
p_norm.append(LA.norm(fb.distances.l0(original, input_batch.cpu()).detach().numpy())) 
#L1
p_norm.append(LA.norm(fb.distances.l1(original, input_batch.cpu()).detach().numpy()))
#L2
p_norm.append(LA.norm(fb.distances.l2(original, input_batch.cpu()).detach().numpy()))
#Linf
p_norm.append(LA.norm(fb.distances.linf(original, input_batch.cpu()).detach().numpy()))
print(p_norm)