#!/usr/local/bin/python3
from igraph import Graph, plot, config, PrecalculatedPalette, VertexClustering
from gurobipy import GRB, LinExpr, Env
import matplotlib.pyplot as plt
from os import path, makedirs
from random import random
import gurobipy as gp
from scipy import io
import argparse
import csv


from sys import argv

version =  "1.0.0"

# Checks if "value" is a nonnegative integer
def check_nonnegative(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("%s is an invalid nonnegative int value" % value)
    return ivalue

# Checks if "value" is a float between 0 and 1
def check_density(value):
    ivalue = float(value)
    if ivalue < 0 or ivalue > 1:
        raise argparse.ArgumentTypeError("%s is an invalid density value. Density should be between 0 and 1." % value)
    return ivalue

# Checks if "value" is a string ending with ".mtx"
def check_mtx_file(value):
    ivalue = str(value)
    if (len(ivalue) < 5 and not ivalue.endswith('.mtx')):
        raise argparse.ArgumentTypeError("%s is an invalid file name. You have to provide a file with .mtx extension." % value)

# Parses command line arguments
def parseArguments ():
    parser = argparse.ArgumentParser(
                        prog=argv[0],
                        description='Bipartition undirected graphs with Gurobi.',
                        epilog='Text at the bottom of help')
    
    parser.add_argument('-i', '--input', metavar="INPUT FILE DIRECTORY",
                        help="Specify the input file directory for your graph. It MUST be a Matrix Market File (.mtx), and MUST NOT include any negative numbers in the adjacency matrix. Graph partitioner works both with a weighted adjacency matrix and an unweighted adjacency matrix.",
                        required=False
                        )
    parser.add_argument('-r', '--random',
                        help="Provide this flag if you want to experiment with random Erdős–Rényi graphs. If you also provide -i argument,the program will first partition the graph in the input file, then partition the random graphs.",
                        action="store_true")
    parser.add_argument('-n', '--number', metavar="NUMBER OF RANDOM GRAPHS TO PARTITION",
                        type=check_nonnegative,
                        default=1,
                        help="Number of random graphs to partition. Need to be specified if -r is given. (Default: 1)",
                        required=False)
    parser.add_argument('-s', '--size', metavar="SIZE OF THE NUMBER OF RANDOM GRAPHS TO PARTITION",
                        type=check_nonnegative,
                        help="Size (number of vertices) of the random graphs. Need to be specified if -r is given. (Default: 10)",
                        default=10,
                        required=False
                        )
    parser.add_argument('-d', '--density', metavar="DENSITY OF THE NUMBER OF RANDOM GRAPHS TO PARTITION",
                        help="Density of the random graphs. Need to be specified if -r is given. (Default: 0.1)",
                        default=0.1,
                        type=check_density,
                        required=False)
    parser.add_argument('-l', '--log', metavar="LOG FILE DIRECTORY",
                        help="Provide a log file name to log Gurobi's optimization process.",
                        required=False)
    parser.add_argument('-w', '--weighted',
                        help="Provide this flag if you want your random graphs to be weighted. You don't need this flag for your input graph (-i).",
                        action="store_true")
    parser.add_argument('-p', '--plot',
                        help="Provide this flag if you want your graphs to be plotted.",
                        action="store_true")
    parser.add_argument('-pDir', '--plotDir',
                        help="Provide a directory to store the plots. Needs -p flag. (Default: The directory of the program.)",
                        required=False)
    parser.add_argument('--version', action='version', version='%(prog)s ' + version)

    args = parser.parse_args()        

    if (args.input == None and args.random == False):
        print("Warning: Neither -i nor -r is given. The program won't partition any graphs!\n")

        parser.print_help()

    return args

# Plots a graph
def plotGraph(g: Graph, clusters: list, runtime: float, objVal: float, maxWeight: float, minWeight: float, name: str, plotDir: str):
    # Plotting
    config['plotting.backend'] = 'matplotlib'
    config["plotting.palette"] = "rainbow"

    communities = VertexClustering(g, clusters)

    print("Clusters")
    print(communities)
        
    num_communities = len(communities)
    palette = PrecalculatedPalette(["lightblue", "yellowgreen", "lightgray"])
    for i, community in enumerate(communities):
        g.vs[community]["color"] = i
        community_edges = g.es.select(_within=community)
        community_edges["color"] = i

    if g.vcount() < 50:
        for vertex in g.vs:
            vertex["label"] = vertex.index

    isWeightless = maxWeight == minWeight

    if ((not isWeightless)):
        for edge in g.es:
            edge["label"] = str(round(edge["weight"], 1))
        
    layout = g.layout("kk")
    fig, ax = plt.subplots()

    plot(g,
         layout=layout,
         palette=palette,
         vertex_size=12 if g.vcount() <= 100 else 4,
         edge_width=[0.5 + weight / (maxWeight - minWeight) * 2 if not isWeightless else 2.5 for weight in g.es["weight"] ],
         vertex_label_size = 7)

    # Add the objective value as text in the right top corner
    plt.title(f"{'Weightless' if isWeightless else 'Weighted'}, {g.vcount():n} vertices, {g.density():.3%} density",
              fontdict=dict(fontweight='bold', fontsize=14))

    totalCutsText = "Total Cuts: " +  (f"{objVal:n}" if isWeightless else f"{round(objVal, 3):.3f}")

    plt.text(.98, .98, f'{totalCutsText}\nRuntime (s): {round(runtime, 3)}',
             transform=plt.gca().transAxes,
             verticalalignment='top',
             horizontalalignment='right',
             bbox=dict(facecolor='white',alpha=0.2, boxstyle='round,pad=0.5'),
             fontsize=14)

    # Create a custom color legend
    legend_handles = []
    for i in range(num_communities):
        handle = ax.scatter(
            [], [],
            s=100,
            facecolor=palette.get(i),
            edgecolor="k",
            label=i,
        )
        legend_handles.append(handle)
    ax.legend(
        handles=legend_handles,
        title='Cluster:',
        bbox_to_anchor=(0, 1.0),
        bbox_transform=ax.transAxes,
    )

    if (plotDir):
        if not path.exists(plotDir):
            makedirs(plotDir)
        plt.savefig(f"{plotDir}/{name}.svg")
    else:
        plt.savefig(f"{name}.svg")
    
    
def write_to_csv(data):

    # CSV file path
    csv_file_path = 'algoData.csv'

    # Check if the file exists
    file_exists = path.isfile(csv_file_path)

    # Write headers if the file doesn't exist
    with open(csv_file_path, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        if not file_exists:
            # Add headers
            csv_writer.writerow(['size', 'edge-count','density', 'weighted', 'objval', 'runtime', 'itercount'])
        
        # Append data
        csv_writer.writerow(data)
        
# Partitions a graph using Gurobi
def graphPartitioner(g: Graph, log: str, plot: bool, plotDir: str, modelName: str):
   
    clusters = [0] * g.vcount()

    # Create a new model
    m = gp.Model(modelName) if log == None else gp.Model(modelName, Env(log)) 
    
    try:
        clusterVars = dict()
        edges = dict()
        objective = LinExpr()

        for vertex in g.vs:
            # Add variable to the model
            clusterVar = m.addVar(vtype=GRB.BINARY, name=f"node_{vertex.index}")
            clusterVars[str(vertex.index)] = clusterVar

        for edge in g.es:
            if edge.is_loop():
                continue
            source, target = str(edge.source), str(edge.target)
            # Add variable to the model
            edgeVar = m.addVar(vtype=GRB.BINARY, name=f"edge_{source}_{target}")
            edges[f"{source}_{target}"] = edge["weight"]
            objective.addTerms(edge["weight"], edgeVar)

            m.addConstr(clusterVars[source] - clusterVars[target] - edgeVar <= 0, f"Connected_nodes_in_the_same_partition_{source}_{target}_l")
            m.addConstr(clusterVars[source] - clusterVars[target] + edgeVar >= 0, f"Connected_nodes_in_the_same_partition_{source}_{target}_u")

        #Cluster size constraint
        m.addConstr(gp.quicksum(clusterVars.values()) == g.vcount() // 2, "cluster_count")

        # Set objective
        m.setObjective(objective, GRB.MINIMIZE)

        # Optimize model
        m.optimize()

#        print("---------------------")
#        print("Edges need to be cut:")
        for v in m.getVars():
            if v.X == 1:
                parts = v.VarName.split('_')

                if parts[0] == 'node':
                    try:
                        # Convert the index part to an integer
                        index = int(parts[1])
                
                        # Use the extracted index
                        clusters[index] = 1
                    except ValueError:
                        # Handle the case where the part after "node_" is not a valid integer
                        print("Invalid index format")

                elif parts[0] == 'edge':
                    cutEdgeId = g.get_eid(int(parts[1]), int(parts[2]))
                    g.es[cutEdgeId]['color'] = 2

#                    print(f"{parts[1]}-{parts[2]}\tweight: {g.es[cutEdgeId]['weight']:.3f}")
            
#        print("---------------------")
#        print(f"Objective: {m.ObjVal:n}")
#        print("---------------------")

    except gp.GurobiError as e:
        print(f"Error code {e.errno}: {e}")

    except AttributeError:
        print("Encountered an attribute error")
    
    
    maxWeight = max(g.es["weight"])
    minWeight = min(g.es["weight"])
    write_to_csv([g.vcount(), g.ecount(), g.density(), 0 if maxWeight == minWeight else 1, round(m.ObjVal,3), m.Runtime, int(m.IterCount)])

    if (plot):
        plotGraph(g, clusters, m.Runtime, m.ObjVal, maxWeight, minWeight, modelName, plotDir)


def main():
    args = parseArguments()

    if (args.input != None):
        mat3 = io.mmread('mycielskian5')

        if (mat3.min() < 0):
            print("Negative values detected in the input matrix. Graph partitioner can't parse graph with negative edge weights.")
        else:
            g = Graph.Weighted_Adjacency(mat3, "undirected")
            graphPartitioner(g, args.log, args.plot, args.plotDir, "inputGraph")


    if (args.random):
        for i in range(args.number):
            g = Graph.Erdos_Renyi(n=args.size, p=args.density, directed=False, loops=False)
            if (args.weighted):
                for e in g.es:
                    e["weight"] = 1 + round(random() * 4, ndigits=3) # Weights are random numbers from 1 to 5.
            else:
                for e in g.es:
                    e["weight"] = 1
            graphPartitioner(g, args.log, args.plot, args.plotDir, f"randomGraph_{i}")

if __name__ == "__main__":
    main()