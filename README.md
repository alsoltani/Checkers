## Checkers

###### Abstract

This is an implementation of an agent to play checkers/draughts, based on Monte Carlo Tree Search and Rapid Action Value Estimation. 

###### Monte Carlo Tree Search

The key idea is to simulate many thousands of random games from the current position, using self-play. New positions are added into a search tree, and each node of the tree contains a value that predicts who will win from that position.     
These predictions are updated by Monte-Carlo simulation: the value of a node is simply the average outcome of all simulated games that visit the position.     
The search tree is used to guide simulations along promising paths, by selecting the child node with the highest potential value. This results in a highly selective search that very quickly identifies good
move sequences.

###### Improvements

Heuristic methods could be used at the initialization of each new node.    
Furthermore, one drawback of MCTS is the large number of simulations needed to obtain accurate solutions. Currently, a timer is used to limit its number to an acceptable rate that would prevent us from hitting timeout on HackerRank & similar challenges.

###### Results

At the time of writing, the best MCTS-based agent reached a score of 43.89 on HackerRank (28th/135).

###### Abstract

"Monte-Carlo Tree Search and Rapid Action Value
Estimation in Computer Go", Sylvain Gelly & al., 2011.