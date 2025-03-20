import json
import logging
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TNode:
    def __init__(self, type_name):
        self.type_name = type_name
        self.subtypes = []

    def add_subtype(self, subtype):
        self.subtypes.append(subtype)

    def __repr__(self):
        return f"TNode({self.type_name})"

    def __hash__(self):
        return hash(self.type_name)

    def __eq__(self, other):
        return isinstance(other, TNode) and self.type_name == other.type_name

class DEdge:
    def __init__(self, from_node, to_node):
        self.from_node = from_node
        self.to_node = to_node

    def __repr__(self):
        return f"DEdge({self.from_node.type_name} -> {self.to_node.type_name})"

class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = []

    def add_node(self, type_name):
        # import pdb; pdb.set_trace()
        if type_name not in self.nodes:
            self.nodes[type_name] = TNode(type_name)
        return self.nodes[type_name]

    def add_edge(self, from_type, to_type):
        from_node = self.add_node(from_type)
        to_node = self.add_node(to_type)
        from_node.add_subtype(to_node)
        self.edges.append(DEdge(from_node, to_node))

    def detect_cycles(self):
        visited = set()
        stack = set()
        cycles = []

        def visit(node):
            if node in stack:
                return [node]
            if node in visited:
                return []
            visited.add(node)
            stack.add(node)
            for subtype in node.subtypes:
                cycle = visit(subtype)
                if cycle:
                    cycle.append(node)
                    if cycle[0] == node:
                        cycles.append(cycle)
                        return []
                    return cycle
            stack.remove(node)
            return []

        for node in self.nodes.values():
            visit(node)

        return cycles

    def dump_graph(self, filename):
        with open(filename, 'w') as f:
            for edge in self.edges:
                f.write(f"{edge.from_node.type_name} -> {edge.to_node.type_name}\n")

def read_node_types(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    file_path = '/u/anag/cov1/release/convert-vcs/vcs-ml/vcs_cleanup/bash2python/node_types.json'
    node_types = read_node_types(file_path)

    graph = Graph()

    for node_type in node_types:
        type_name = node_type['type']
        if 'subtypes' in node_type:
            for subtype in node_type['subtypes']:
                graph.add_edge(type_name, subtype['type']) 

    cycles = graph.detect_cycles()
    if cycles:
        logging.info("Cycles detected:")
        for cycle in cycles:
            logging.info(" -> ".join(node.type_name for node in cycle))
    else:
        logging.info("No cycles detected.")

    graph.dump_graph('graph_output.txt')

if __name__ == "__main__":
    main()
