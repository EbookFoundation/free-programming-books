This is a link to Data structures and algorithms.
It is provided free by (School of computer Science)
the link is - [https://www.cs.bham.ac.uk/~jxb/DSA/dsa.pdf]

**INDICE**
Introduction 5
1.1 Algorithms as opposed to programs . . . . . . . . . . . . . . . . . . . . . . . . . 5
1.2 Fundamental questions about algorithms . . . . . . . . . . . . . . . . . . . . . . 6
1.3 Data structures, abstract data types, design patterns . . . . . . . . . . . . . . . 7
1.4 Textbooks and web-resources . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
1.5 Overview . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
2 Arrays, Iteration, Invariants 9
2.1 Arrays . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.2 Loops and Iteration . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
2.3 Invariants . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
3 Lists, Recursion, Stacks, Queues 12
3.1 Linked Lists . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
3.2 Recursion . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
3.3 Stacks . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
3.4 Queues . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
3.5 Doubly Linked Lists . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
3.6 Advantage of Abstract Data Types . . . . . . . . . . . . . . . . . . . . . . . . . 20
4 Searching 21
4.1 Requirements for searching . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 21
4.2 Specification of the search problem . . . . . . . . . . . . . . . . . . . . . . . . . 22
4.3 A simple algorithm: Linear Search . . . . . . . . . . . . . . . . . . . . . . . . . 22
4.4 A more efficient algorithm: Binary Search . . . . . . . . . . . . . . . . . . . . . 23
5 Efficiency and Complexity 25
5.1 Time versus space complexity . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
5.2 Worst versus average complexity . . . . . . . . . . . . . . . . . . . . . . . . . . 25
5.3 Concrete measures for performance . . . . . . . . . . . . . . . . . . . . . . . . . 26
5.4 Big-O notation for complexity class . . . . . . . . . . . . . . . . . . . . . . . . . 26
5.5 Formal definition of complexity classes . . . . . . . . . . . . . . . . . . . . . . . 29
6 Trees 31
6.1 General specification of trees . . . . . . . . . . . . . . . . . . . . . . . . . . . . 31
6.2 Quad-trees . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 32
6.3 Binary trees . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 33
2
6.4 Primitive operations on binary trees . . . . . . . . . . . . . . . . . . . . . . . . 34
6.5 The height of a binary tree . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 36
6.6 The size of a binary tree . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 37
6.7 Implementation of trees . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 37
6.8 Recursive algorithms . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 38
7 Binary Search Trees 40
7.1 Searching with arrays or lists . . . . . . . . . . . . . . . . . . . . . . . . . . . . 40
7.2 Search keys . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 40
7.3 Binary search trees . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41
7.4 Building binary search trees . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41
7.5 Searching a binary search tree . . . . . . . . . . . . . . . . . . . . . . . . . . . . 42
7.6 Time complexity of insertion and search . . . . . . . . . . . . . . . . . . . . . . 43
7.7 Deleting nodes from a binary search tree . . . . . . . . . . . . . . . . . . . . . . 44
7.8 Checking whether a binary tree is a binary search tree . . . . . . . . . . . . . . 46
7.9 Sorting using binary search trees . . . . . . . . . . . . . . . . . . . . . . . . . . 47
7.10 Balancing binary search trees . . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
7.11 Self-balancing AVL trees . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
7.12 B-trees . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 49
8 Priority Queues and Heap Trees 51
8.1 Trees stored in arrays . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 51
8.2 Priority queues and binary heap trees . . . . . . . . . . . . . . . . . . . . . . . 52
8.3 Basic operations on binary heap trees . . . . . . . . . . . . . . . . . . . . . . . 53
8.4 Inserting a new heap tree node . . . . . . . . . . . . . . . . . . . . . . . . . . . 54
8.5 Deleting a heap tree node . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 55
8.6 Building a new heap tree from scratch . . . . . . . . . . . . . . . . . . . . . . . 56
8.7 Merging binary heap trees . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 58
8.8 Binomial heaps . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 59
8.9 Fibonacci heaps . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 61
8.10 Comparison of heap time complexities . . . . . . . . . . . . . . . . . . . . . . . 62
9 Sorting 63
9.1 The problem of sorting . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63
9.2 Common sorting strategies . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 64
9.3 How many comparisons must it take? . . . . . . . . . . . . . . . . . . . . . . . 64
9.4 Bubble Sort . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 66
9.5 Insertion Sort . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 67
9.6 Selection Sort . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 69
9.7 Comparison of O(n
2
) sorting algorithms . . . . . . . . . . . . . . . . . . . . . . 70
9.8 Sorting algorithm stability . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 71
9.9 Treesort . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 71
9.10 Heapsort . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 72
9.11 Divide and conquer algorithms . . . . . . . . . . . . . . . . . . . . . . . . . . . 74
9.12 Quicksort . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 75
9.13 Mergesort . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 79
9.14 Summary of comparison-based sorting algorithms . . . . . . . . . . . . . . . . . 81
3
9.15 Non-comparison-based sorts . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 81
9.16 Bin, Bucket, Radix Sorts . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 83
10 Hash Tables 85
10.1 Storing data . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 85
10.2 The Table abstract data type . . . . . . . . . . . . . . . . . . . . . . . . . . . . 85
10.3 Implementations of the table data structure . . . . . . . . . . . . . . . . . . . . 87
10.4 Hash Tables . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 87
10.5 Collision likelihoods and load factors for hash tables . . . . . . . . . . . . . . . 88
10.6 A simple Hash Table in operation . . . . . . . . . . . . . . . . . . . . . . . . . . 89
10.7 Strategies for dealing with collisions . . . . . . . . . . . . . . . . . . . . . . . . 90
10.8 Linear Probing . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 92
10.9 Double Hashing . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 94
10.10Choosing good hash functions . . . . . . . . . . . . . . . . . . . . . . . . . . . . 96
10.11Complexity of hash tables . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 96
11 Graphs 98
11.1 Graph terminology . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 99
11.2 Implementing graphs . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 100
11.3 Relations between graphs . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 102
11.4 Planarity . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 103
11.5 Traversals – systematically visiting all vertices . . . . . . . . . . . . . . . . . . . 104
11.6 Shortest paths – Dijkstra’s algorithm . . . . . . . . . . . . . . . . . . . . . . . . 105
11.7 Shortest paths – Floyd’s algorithm . . . . . . . . . . . . . . . . . . . . . . . . . 111
11.8 Minimal spanning trees . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 113
11.9 Travelling Salesmen and Vehicle Routing . . . . . . . . . . . . . . . . . . . . . . 117
12 Epilogue 118
A Some Useful Formulae 119
A.1 Binomial formulae . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 119
A.2 Powers and roots . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 119
A.3 Logarithms . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 119
A.4 Sums . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 120
A.5 Fibonacci numbers . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 121
