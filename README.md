# CMPE 492 Project: Partitioning Undirected Graphs

Graduation project that aims to partition undirected graphs to 2 equal sized subgraphs by cutting minimum number of edges. Edges can have positive weights.

## Example Output

30 vertices with weightless edges | 80 vertices with weightless edges
:-------------------------:|:-------------------------:
![example partition 1](https://github.com/araldortogul/CMPE492_Partitioning_Undirected_Graphs/blob/main/docs/final%20report/latex/figures/erdos-1.svg)  |  ![example partition 2](https://github.com/araldortogul/CMPE492_Partitioning_Undirected_Graphs/blob/main/docs/final%20report/latex/figures/erdos-2.svg)

20 vertices with weighted edges | 50 vertices with weidghted edges
:-------------------------:|:-------------------------:
![example partition 3](https://github.com/araldortogul/CMPE492_Partitioning_Undirected_Graphs/blob/main/docs/final%20report/latex/figures/erdos-3.svg)  |  ![example partition 4](https://github.com/araldortogul/CMPE492_Partitioning_Undirected_Graphs/blob/main/docs/final%20report/latex/figures/erdos-4.svg)

# Running the Program

> [!IMPORTANT] 
> The program requires a Gurobi license to run. For more information about Gurobi's licenses, please check [Gurobi's website](https://www.gurobi.com/downloads/).

The program can be run with the following command:

```console
./graph_partitioner.py
```
