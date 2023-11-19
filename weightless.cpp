#include "gurobi_c++.h"
#include <iostream>
#include <string>
#include <cstdlib>
#include <vector>
#include <deque>
#include <utility>
#include <algorithm>
#include <fstream>

using namespace std;

static const vector<string> reservedOptions = {"-i", "--input", "-n", "--number", "-l", "--log", "-d", "--density", "-s", "--size"};

int adjacency2dto1d(int from, int to)
{
     return from * (from - 1) / 2 + to;
}

static void show_usage(string name)
{
     cerr << "Usage: " << name << " <option(s)>" << endl
          << "Options:" << endl
          << "\t-i,--input\tINPUT FILE\tSpecify the input file's destination path." << endl
          << "\t-n,--number\t# OF GRAPHS\tSpecify the number of graphs. Will not be used if -i option is given." << endl
          << "\t-l,--log\tLOG FILE\tSpecify the destination path. Default: " << name << ".log" << endl
          << "\t-d,--density\tDENSITY\t\tSpecify the density of Erdös-Renyi random graphs. Will not be used if -i option is given." << endl
          << "\t-s,--size\tSIZE OF GRAPHS\tSpecify the size of the graphs. Will not be used if -i option is given." << endl
          << endl;
}

static bool isArgumentValueGivenProperly(string arg, string val, string name)
{

     if (find(reservedOptions.begin(), reservedOptions.end(), val) != reservedOptions.end())
     {
          cerr << arg << " argument is not given properly." << endl;
          show_usage(name);
          return false;
     }
     return true;
}

static bool readArguments(int argc, char *argv[], string *input, string *log, int *graphSize, int *numberOfGraphs, double *probability)
{
     const string name = argv[0];
     // Read command line arguments
     if (argc % 2 == 0 || argc < 2)
     {
          show_usage(argv[0]);
          return false;
     }
     for (int i = 1; i < argc; i += 2)
     {
          const string arg = argv[i];
          if (arg == "-i" || arg == "--input")
          {
               const string inputFile = argv[i + 1];
               if (!isArgumentValueGivenProperly(arg, inputFile, name))
               {
                    return false;
               }
               *input = inputFile;
          }
          // else if (arg == "-o")
          // {
          //      const string outputFile = argv[i];
          // }
          else if (arg == "-s" || arg == "--size")
          {
               const string size = argv[i + 1];
               if (!isArgumentValueGivenProperly(arg, size, name))
               {
                    return false;
               }
               *graphSize = stoi(size);
          }
          else if (arg == "-n" || arg == "--number")
          {
               const string graphCount = argv[i + 1];
               if (!isArgumentValueGivenProperly(arg, graphCount, name))
               {
                    return false;
               }
               *numberOfGraphs = stoi(graphCount);
          }
          else if (arg == "-d" || arg == "--density")
          {
               const string prob = argv[i + 1];
               if (!isArgumentValueGivenProperly(arg, prob, name))
               {
                    return false;
               }
               *probability = stod(prob);
          }
          else if (arg == "-l" || arg == "--log")
          {
               const string logFile = argv[i + 1];
               if (!isArgumentValueGivenProperly(arg, logFile, name))
               {
                    return false;
               }
               *log = logFile;
          }
          else
          {
               cerr << "Unknown parameter entered. (" << arg << ")" << endl;
               show_usage(name);
               return false;
          }
     }
     return true;
}

static void generateAdjacencyMatrixFromInput(const string *const input, const int size, bool adjacency[], vector<int> cuttableEdges[], const int *cuttableEdgeCount)
{
     int i = 1, j = 0, index = 0;

     ifstream inputFile;
     inputFile.open(*input);
     string word;

     for (int from = 1; from < size; from++)
     {
          for (int to = 0; to < from; to++)
          {
               inputFile >> word;

               int isAdjacent = word == "1";
               adjacency[index] = isAdjacent;
               if (isAdjacent)
               {
                    cuttableEdges[from - 1].push_back(to);
                    cuttableEdgeCount++;
               }
               index++;
          }
     }
}

static void generateRandomAdjacencyMatrix(const int graphCount, const int size, const double density, bool adjacency[], vector<int> cuttableEdges[], int *cuttableEdgeCount)
{

     int i = 1, j = 0, index = 0;

     for (int from = 1; from < size; from++)
     {
          for (int to = 0; to < from; to++)
          {

               double random = ((double)rand()) / RAND_MAX;
               int isAdjacent = random <= density;
               adjacency[index] = isAdjacent;
               if (isAdjacent)
               {
                    cuttableEdges[from - 1].push_back(to);
                    (*cuttableEdgeCount)++;
               }
               index++;
          }
     }
}

static void buildAndRunGurobiModel(string *const log, const int cuttableEdgeCount, const int graphSize, const double density, vector<int> cuttableEdges[])
{

     // Create an environment
     GRBEnv env = GRBEnv(true);
     env.set("LogFile", *log);
     env.start();

     // Create an empty model
     GRBModel model = GRBModel(env);

     // Create variables
     GRBVar x[cuttableEdgeCount];
     GRBVar y[graphSize];

     // Objective expression
     GRBLinExpr totalCuts = 0;

     // Constraints
     GRBLinExpr totalNodesInPartition1 = 0;

     int index = 0;
     for (int from = 0; from < graphSize; from++)
     {

          y[from] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY, "node_" + to_string(from));
          totalNodesInPartition1 += y[from];
     }

     int cuttableEdgeIndex = 0;
     for (int from = 1; from < graphSize; from++)
     {
          for (vector<int>::iterator to = cuttableEdges[from - 1].begin(); to != cuttableEdges[from - 1].end(); to++)
          {
               x[cuttableEdgeIndex] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY, "cut_" + to_string(from) + "_" + to_string(*to));

               totalCuts += x[cuttableEdgeIndex];

               model.addConstr(y[from] - y[*to] - x[cuttableEdgeIndex] <= 0, "Connected_nodes_in_the_same_partition" + to_string(from) + "_" + to_string(*to) + "l");
               model.addConstr(y[from] - y[*to] + x[cuttableEdgeIndex] >= 0, "Connected_nodes_in_the_same_partition" + to_string(from) + "_" + to_string(*to) + "_u");

               cuttableEdgeIndex++;
          }
     }
     // Set objective: maximize x + y + 2 z
     model.setObjective(totalCuts, GRB_MINIMIZE);

     // Add constraint: x + 2 y + 3 z <= 4
     model.addConstr(totalNodesInPartition1 == graphSize / 2, "Equal_partition_sizes");

     // Optimize model
     model.optimize();

     // model.write("model.lp");

     /*
     std::cout << "Partitions:" << endl;
     for (int node = 0; node < graphSize; node++)
     {
          std::cout << y[node].get(GRB_StringAttr_VarName) << " "
                    << y[node].get(GRB_DoubleAttr_X) << endl;
     }
     std::cout << endl;
     for (int edge = 0; edge < cuttableEdgeCount; edge++)
     {
          std::cout << x[edge].get(GRB_StringAttr_VarName) << " "
                    << x[edge].get(GRB_DoubleAttr_X) << endl;
     }
     std::cout << endl;
     */
     std::cout << "Obj: " << model.get(GRB_DoubleAttr_ObjVal) << endl;

     ofstream output;
     output.open("solutions.csv", ofstream::app);
     output << graphSize << "," << density << "," << model.get(GRB_DoubleAttr_Runtime) << "," << model.get(GRB_DoubleAttr_ObjVal) << "," << model.get(GRB_DoubleAttr_IterCount) << endl;
     output.close();
}

int main(int argc, char *argv[])
{
     srand((unsigned)time(NULL));
     const string name = argv[0];

     string input = "", log = name + ".log";
     int graphSize = -1, numberOfGraphs = -1;
     double density = -1;
     char inputType = 'l';

     // Read command line arguments
     if (!readArguments(argc, argv, &input, &log, &graphSize, &numberOfGraphs, &density))
     {
          return 1;
     }

     int totalPossibleEdgeCount = (graphSize - 1) * (graphSize) / 2;
     bool adjacency[totalPossibleEdgeCount];
     vector<int> cuttableEdges[graphSize - 1];
     int cuttableEdgeCount = 0;

     bool isInputGiven = !input.empty();

     // If graph is given in input
     if (isInputGiven)
     {
          // read input and build graph
          generateAdjacencyMatrixFromInput(&input, graphSize, adjacency, cuttableEdges, &cuttableEdgeCount);

          std::cout << "Lower triangle of the adjacency matrix:" << endl;
          for (int i = 1; i < graphSize; i++)
          {
               for (int j = 0; j < i; j++)
               {
                    std::cout << (adjacency[adjacency2dto1d(i, j)] ? 1 : 0) << " ";
               }
               std::cout << endl;
          }
          std::cout << endl;

          // TODO: Calculate density

          //  run gurobi
          try
          {
               buildAndRunGurobiModel(&log, cuttableEdgeCount, graphSize, density, cuttableEdges);
          }
          catch (GRBException e)
          {
               cerr << "Error code = " << e.getErrorCode() << endl;
               cerr << e.getMessage() << endl;
          }
          catch (...)
          {
               cerr << "Exception during optimization" << endl;
          }
     }
     // If the graph will be generated randomly
     else
     {
          for (int i = 0; i < numberOfGraphs; i++)
          {
               // build graphs
               generateRandomAdjacencyMatrix(numberOfGraphs, graphSize, density, adjacency, cuttableEdges, &cuttableEdgeCount);

               std::cout << "Lower triangle of the adjacency matrix:" << endl;
               for (int i = 1; i < graphSize; i++)
               {
                    for (int j = 0; j < i; j++)
                    {
                         std::cout << (adjacency[adjacency2dto1d(i, j)] ? 1 : 0) << " ";
                    }
                    std::cout << endl;
               }
               std::cout << endl;

               // run gurobi
               try
               {
                    buildAndRunGurobiModel(&log, cuttableEdgeCount, graphSize, density, cuttableEdges);
               }
               catch (GRBException e)
               {
                    cerr << "Error code = " << e.getErrorCode() << endl;
                    cerr << e.getMessage() << endl;
               }
               catch (...)
               {
                    cerr << "Exception during optimization" << endl;
               }

               // clean
               cuttableEdgeCount = 0;
               for (int i = 0; i < graphSize - 1; i++)
               {
                    cuttableEdges[i].clear();
               }
          }
     }

     return 0;
}
