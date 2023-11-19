GUROBI_HOME = /Library/gurobi1003/macos_universal2

INC      = $(GUROBI_HOME)/include/
CC       = gcc
CPP      = g++
CARGS    = -std=c++11 -m64 -g
CLIB     = -L$(GUROBI_HOME)/lib -lgurobi100
CPPLIB   = -L$(GUROBI_HOME)/lib -lgurobi_c++ -lgurobi100


all: weightless_graph_partitioner

weightless_graph_partitioner: weightless.cpp
	$(CPP) $(CARGS) -o weightless_graph_partitioner weightless.cpp -I$(INC) $(CPPLIB) -lm
	
