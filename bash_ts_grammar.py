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

def find_dependencies(node, dependencies, parent_type=None):
    if isinstance(node, dict):
        for key, value in node.items():
            logging.debug(f"key: {key}, value: {value}")
            if key == "type" and parent_type != value:
                dependencies[parent_type].add(value)
                continue
            find_dependencies(value, dependencies, parent_type)
    elif isinstance(node, list):
        logging.debug(f"node: {node}, parent_type: {parent_type}")    
        for item in node:
            find_dependencies(item, dependencies, parent_type)

def print_dependencies(dependencies):
    for parent, children in dependencies.items():
        print(f"{parent}: {', '.join(children)}")

def main():
    file_path = 'c:\\Users\\anagx\\DevWorks\\bash-py\\node_types.json'
    node_types = read_node_types(file_path)

    graph = Graph()

    for node_type in node_types:
        node = graph.add_node(node_type['type'])
        dependencies = defaultdict(set)
        find_dependencies(node_type, dependencies, node_type['type'])
        # print_dependencies(dependencies)
        for dependency in dependencies[node_type['type']]:
            graph.add_edge(node_type['type'], dependency)

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
