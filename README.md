# Multi-robot Task Allocation and Planning under Linear Temporal Logic Specifications
We consider the problem of optimally allocating tasks, expressed as global Linear Temporal Logic (LTL) specifications, to teams of heterogeneous mobile robots. The robots are classified in different types that capture their dif- ferent capabilities, and each task may require robots of multiple types. The specific robots assigned to each task are immaterial, as long as they are of the desired type. Given a discrete workspace, our goal is to design paths, i.e., sequences of discrete states, for the robots so that the LTL specification is satisfied. To obtain a scalable solution to this complex temporal logic task allocation problem, we propose a hierarchical approach that first allocates specific robots to tasks using the information about the tasks contained in the Nondeterministic Bu ̈chi Automaton (NBA) that captures the LTL specification, and then designs low- level executable plans for the robots that respect the high-level assignment. Specifically, we first prune and relax the NBA by removing all negative atomic propositions. This step is motivated by “lazy collision checking” methods in robotics and allows to simplify the planning problem by checking constraint satisfaction only when needed. Then, we extract sequences of subtasks from the relaxed NBA along with their temporal orders, and formulate a Mixed Integer Linear Program (MILP) to allocate these subtasks to the robots. Finally, we define generalized multi-robot path planning problems to obtain low-level executable robot plans that satisfy both the high-level task allocation and the temporal constraints captured by the negative atomic propositions in the original NBA. We show that our method is complete for a subclass of LTL that covers a broad range of tasks and present numerical simulations demonstrating that it can generate paths with lower cost, considerably faster than existing methods.

# Install
 The code is tesed using Python 3.10.12.
### Develop via Conda
 Following the instruction:
```bash
cd /path/to/LTL_MRTA
conda env create -f environment.yml
```
### Import as package
```bash
cd /path/to/LTL_MRTA
pip install -e .
```
### Install ltl2ba
Download the software `LTL2BA` from this [link](http://www.lsv.fr/~gastin/ltl2ba/index.php), and follow the instructions to generate the exectuable `ltl2ba` and then copy it into the root folder `LTL_MRTA`.
### Install solver [Gurobi](https://www.gurobi.com)
# Example

### Simulation I
$$
\begin{align}
\phi_1 &= \lozenge \left(\left(\pi_{2,1}^{2,1}\wedge \neg \pi_{2,1}^{3}\right) \wedge  \lozenge \pi_{2,1}^{3,1}\right)  \wedge \lozenge \pi_{1,2}^{4} \wedge \neg \pi_{2,1}^{3} \ U\  \pi_{1,2}^{4} \\
\phi_2 &= \square \lozenge \left(\pi_{1,1}^{2,1} \wedge \lozenge \pi_{1,1}^{3,1}\right)
\end{align}
$$

```bash
# change c to 1, 2
python ./case/case1.py --case=c --partial_or_full=f --only_first --loop --vis --print
```
<video width="320" height="240" controls>
  <source src="/Users/xushengluo/Documents/Code/LTL_MRTA/data/mapp_case1.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

The demo video for case 1.

### Simulation II
$$
\begin{align}
   \phi_3 &= \  \square \lozenge (\pi_{2,1}^{2,1} \wedge \lozenge (\pi_{2,1}^{3,1} \wedge \lozenge (\pi_{2,1}^{4,1} \wedge \lozenge \pi_{2,1}{5,1}  )   )  ), \\
   \phi_4 & = \square \lozenge (\pi_{2,1}^{2,1} \wedge \lozenge \pi_{2,1}^{3,1}) \wedge \square (\pi_{1,1}^{5,2} \Rightarrow \bigcirc (\pi_{1,1}^{5,2} \;U \  \pi_{1,2}^{4})) \wedge \square \neg \pi_{2,1}^{4},\\
   \phi_5  & = \  \lozenge (\pi_{1,2}^{4,1} \wedge \bigcirc (\pi_{1,2}^{4,1} \;U \  \pi_{2,1}^{3})) \wedge \square \lozenge ( \pi_{1,2}^{4,1} \wedge \lozenge \pi_{1,2}^{3,1}), \\
   \phi_6  & = \   \square \lozenge (\pi_{1,1}^{3,1} \ \vee \  \pi_{1,1}^{5,1}) \wedge \square \lozenge \pi_{1,1}^{2,1}  \wedge \square \lozenge (\pi_{2,2}^{3} \ \vee\  \pi_{2,2}^{5}) \wedge \square \neg \pi_{2,1}^{4} \wedge \square \neg \pi_{2,2}^{4}, \\
   \phi_7  & = \   \square \lozenge (\pi_{1,2}^{4} \wedge \bigcirc (\lozenge \neg \pi_{1,2}^{4})) \wedge  \square \lozenge (\pi_{1,1}^{5} \wedge \bigcirc (\lozenge \neg \pi_{1,1}^{5} )) \wedge  \lozenge  (\pi_{3,1}^{3} \wedge \pi_{2,2}^{3}), \\
   \phi_8 & = \  \square \lozenge  (\pi_{2,2}^{4,1} \wedge \lozenge (\pi_{2,2}^{2,1} \wedge \lozenge \pi_{2,2}^{5,1}))  \wedge  \neg \pi_{1,2}^{2} \;U \  \pi_{2,2}^{4,1} \wedge \neg \pi_{1,2}^{5} \; U \  \pi_{2,2}^{4,1} \wedge (\square \lozenge \pi_{2,1}^{5}\  \vee \   \square \lozenge \pi_{2,1}^{3}),
 \end{align}
$$
```bash
# change c to 3, 4, ... 8
python ./case/case2.py --case=c --partial_or_full=f --only_first --loop --vis --print
```

<video width="320" height="240" controls>
  <source src="/Users/xushengluo/Documents/Code/LTL_MRTA/data/mapp_case5.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

The demo video for case 5.


### Simulation III
$$
\begin{align}
     \phi_9 & = \   \square \lozenge \pi_{n,1}^{2} \wedge   \square \lozenge \pi_{n/2,1}^{3} \ \wedge \square \lozenge \pi_{n/2,1}^{4} \wedge \neg \pi_{1,1}^{4} \ U\  (\pi_{1,1}^{5} \wedge \pi_{1,1}^{6}), \\
    \phi_{10} & = \  \lozenge (\pi_{3,1}^{5} \ \vee \  \pi_{3,1}^{6}) \ \wedge   \square \lozenge (\pi_{n/2,1}^{2,1} \wedge \lozenge \pi_{n/2,1}^{4,1}) \wedge  \square \lozenge \pi_{n/4,1}^{3} \wedge \square \neg \pi_{4,1}^{6},
\end{align}
$$
```bash
# change c to 9, 10
python ./case/case3.py --case=c --partial_or_full=f --only_first --loop --vis --print --robot=2 
```
<video width="320" height="240" controls>
  <source src="/Users/xushengluo/Documents/Code/LTL_MRTA/data/mapp_case9.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

The demo video for case 9.

# Citation
```
@article{luo2022temporal,
  title={Temporal logic task allocation in heterogeneous multirobot systems},
  author={Luo, Xusheng and Zavlanos, Michael M},
  journal={IEEE Transactions on Robotics},
  volume={38},
  number={6},
  pages={3602--3621},
  year={2022},
  publisher={IEEE}
}
```