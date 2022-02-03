from numba import cuda

"""
 Bidirectional NN strengthened by rewards

 input image  <->   Nodes
 input audio  <-> 
 output image <->
 output audio <->

Node
- usage score tracks usage and exponentially decays over time  
- strengethened proportionally to usage score when rewarded

Training
- Audio conversation / youtube class = input audio
- When input audio would have been a response, 
  put this data as output audio at t-1
- During training reward is always high with small time values
- During usage, rewards are given via the app with a time value specified
"""

"""
 Single direction NN with feedback loop
 
 input image 0   ->   -> output 0
 input image MN  ->   ->
 output 0        ->   -> 
 output N        ->   -> output N

 Some outputs are actions/classification/etc
 Some outputs are feedback
 Some outputs are both

 Train = backprop desired output at each
 Problem = multiple good outputs
"""

"""
 Memory
 Single layer NN that loops back onto itself.
 It may be a collection of (80, 60, 3) thumbnails
 Otherwise every memory would have to be replaying through
 the entire NN all the time.
 When being recalled it is activated such that it is outgoing
 again.
 What features allow for useful clustering?
 It was a brown piano with curves "like this" -> you can picture it
 but not exactly
"""

"""
 Reward
 Keeping trying different things (this is what it is programmed to do)
 Create connections based upon what it does
 If it got it correct quickly reward strongly over that small time
 If it got it correct slowley reward weakly over that large time

 Trying differnt things = difference sequences of actions (plans)
"""

"""
 Decomposing inputs into features
 Image -> NN -> features

 features = lake + grass + mountains + sky + ...
     lake = dark blue + oval shaped + cold looking ...
     grass = green + wild + blowing in the wind ...
   features are hierarchical, can be described in more detail
           vs less detail
 compare input images with memory based upon general features first
   then more specific
 ex: many matches for grass 
    - less for lawn grass 
    - less for crab grass on the lawn
    - less for yellow crab grass on the lawn of my neighbors house
"""

def main():
    print("Begin")

if __name__ == "__main__":
    main()