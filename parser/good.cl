-- abstract list data structure, implemented following the video tutorial from Dr. Leach.
class List inherits IO{
    isNil(): Bool {true};
    s : String;
    s() : String {s};
    next : List;
    next() : List {next};
    --random expressions to test associativity
    random1 : Int <- (a + b * c) - (d + e) * f;
    randombool: Bool <- (a<b)<c;
    randombool2: Bool <- a.firstcall().secondcall() <= b.secondcall() + a.firstcall();

    sortedInsert( news: String): List {
        if isNil() then
            (new ListNode).init(news, self)
        else
            if news < s then
                (new ListNode).init(news, self)
            else {
                next <- next.sortedInsert(news);
                i <- i + 1;
                self;
            } fi
        fi         
    };

    reverseInsert( news: String): List{
        if isNil() then
            (new ListNode).init(news, self)
        else{
            next <- next.reverseInsert(news);
            self;
        } fi
    };

    insert( news : String) : List {
        (new ListNode).init(news, self)
    };

    remove( search: String): List{
        self
    };

    print() : Object {
        if isNil() then out_string("\n")
        else {
            out_string (s);
            out_string (", ");
            next.print();
        } fi
    };

    print_new_line() : Object {
        if isNil() then 0
        else {
            out_string (s);
            out_string ("\n");
            next.print_new_line();
        } fi
    };

    contains (search : String) : Bool {
        if isNil() then
            false
        else
            if search = s then
                true
            else
                next.contains(search)
            fi
        fi
    };
};

-- concrete list data structure, implemented following the video tutorial from Dr. Leach.
class ListNode inherits List{
    isNil() : Bool {false};


    init( news : String, newnext: List) : List{{
        s <- news;
        next <- newnext;
        self;
    }};

    remove( search: String): List{{
        next <- next.remove(search);
        if search = s then next else self fi;
    }};
};

-- abstract map data structure, implemented following the video tutorial from Dr. Leach.
class Map inherits IO {
    key: String;
    elements: List;
    next : Map;

    isNil(): Bool {true};
    key(): String {key};
    elements() : List { elements};
    next(): Map {next};

    contains (search: String): Bool {
        if isNil() then false else
            if key = search then true
            else next.contains(search) fi
        fi
    };

    insert( search: String, value: String): Map {
        if isNil() then
            (new MapNode).init( search, value, self)
        else
            if search = key then 
                if elements.contains(value) then 
                    self
                else {
                    elements <- elements.sortedInsert(value);
                    self;
                }fi
            else{
                next <- next.insert(search, value);
                self;
            }fi
        fi
    };

    remove (search: String, value :  String): Map{
        if isNil() then self else 
            if search = key then {
                elements <- elements.remove(value);
                self;
            } else {
                next <- next.remove(search, value);
                self;
            }fi
        fi
    };

    get(search: String): List {
        if isNil() then new List else
            if search = key then elements
            else next.get(search) fi
        fi
    };

    print() : Object { 
        if isNil() then out_string("\n") else {
            out_string("Key ");
            out_string(key);
            out_string(": ");
            elements.print();
            next.print();
        } fi
    };
};

-- concrete list data structure, implemented following the video tutorial from Dr. Leach.
class MapNode inherits Map {
    isNil () : Bool {false};

    init(search: String, value: String, therest: Map): MapNode {{
        key <- search;
        elements <- new List;
        elements <- elements.insert(value);
        next <- therest;
        self;
    }};
};

class Main inherits IO {
    myList : List <- new List; --map to keep track of all the vertices
    myMap : Map <- new Map; --map to store the graph structure
    printList : List <- new List; -- list to keep track of the list to be printed at the end
    unvisitedDFSList: List <- new List; -- list for dfs to determine cycle, stores the verteces with "unvisited" state
    visitingDFSList: List <- new List; --list for dfs to determine cycle, stores the verteces with "visiting" state
    visitedDFSList: List <- new List; -- list for dfs to determine cycle, stores the verteces with "visited" state
    visitedTopSortList: List <- new List; --list for dfs for topological sort, stores the verteces with "visited" state
    randombool : Bool <- 1 + 2 * 3 <= 4 * (5/6 + 7 /8);

    -- dfs method used in the detect_cycle()
    dfs_cycle(graph: Map, vertex: String): Bool {
        let result: Bool <- false in
            if visitingDFSList.contains(vertex) then 
                true
                else 
                    if visitedDFSList.contains(vertex) then
                        false
                    else
                        {
                            visitingDFSList <- visitingDFSList.insert(vertex);
                            unvisitedDFSList <- unvisitedDFSList.remove(vertex);
                            let neighbors : List <- graph.get(vertex),
                                done: Bool <- false in
                                while not done loop
                                    if neighbors.isNil() then 
                                        done <- true 
                                    else
                                        if dfs_cycle(graph, neighbors.s()) then{
                                            result <- true;
                                            neighbors <- neighbors.next();
                                        }else
                                            neighbors <- neighbors.next()
                                        fi
                                    fi
                                pool;
                            visitingDFSList <- visitingDFSList.remove(vertex);
                            visitedDFSList <- visitedDFSList.insert(vertex);
                            result;
                        }
                    fi
            fi
    };

    -- detect if a cycle is in the graph, returns true if the graph is cyclic
    detect_cycle(graph : Map): Bool {{
        let done : Bool <- false, 
            curList : List <- myList, 
            tmpString: String <- "" 
        in 
            while not done loop
                if curList.isNil() then
                    done <- true
                else{
                    tmpString <- curList.s();
                    unvisitedDFSList <- unvisitedDFSList.insert(tmpString);
                    curList <- curList.next();
                }fi
            pool;
        
        let done :  Bool <- false,
            curList : List <- myList,
            result: Bool <- false
        in {
            while not done loop
                if curList.isNil() then
                    done <- true
                else
                    if unvisitedDFSList.contains(curList.s()) then{
                        if dfs_cycle(graph, curList.s()) then
                            result <- true
                        else
                            0
                        fi;
                        curList <- curList.next();
                    }else
                        curList <- curList.next()
                    fi
                fi
            pool;
            result;
        };
    }};

    -- dfs for topological sort, marks the vertex as visited and calls dfs_topsort on the unvisited neighbors, adds the current vertex to the printList with tail recursion.
    dfs_topsort(graph: Map, vertex: String): List {{
        visitedTopSortList <- visitedTopSortList.insert(vertex);
        let neighbors : List <- graph.get(vertex),
            done: Bool <- false 
        in
            while not done loop
                if neighbors.isNil() then 
                    done <- true 
                else
                    if not visitedTopSortList.contains(neighbors.s()) then{
                        dfs_topsort(graph, neighbors.s());
                        neighbors <- neighbors.next();
                    }else
                        neighbors <- neighbors.next()
                    fi
                fi
            pool;
        printList <- printList.reverseInsert(vertex);
    }};

    -- performs topological sort on all the vertices to inserts the vertices in the correct order into printList
    topsort(graph: Map): Object {{
        let done: Bool <- false,
            curList : List <- myList
        in
            while not done loop
                if curList.isNil() then
                    done <- true
                else
                    if not visitedTopSortList.contains(curList.s()) then{
                        dfs_topsort(graph, curList.s());
                        curList <- curList.next();
                    }else
                        curList <- curList.next()
                    fi
                fi
            pool;             
    }};

    main() : Object {{
        let done: Bool <- false
        in 
        while not done loop
            let t1: String <- in_string(),
                t2: String <- in_string()
            in {
                if t1 = "" then
                    done <- true
                else{
                    myMap <- myMap.insert(t1, t2); -- adds the task pair to myMap to represent the verteces and edges
                    if not myList.contains(t1) then -- adds the task to myList if it's not already in myList
                        myList <- myList.sortedInsert(t1)
                    else
                            0
                    fi;
                    if not myList.contains(t2) then -- adds the task to myList if it's not already in myList
                        myList <- myList.sortedInsert(t2)
                    else
                        0 
                    fi;
                } fi;
            }
        pool;

        if detect_cycle(myMap) then
            out_string("cycle\n") -- prints "cycle" if a cycle is detected
        else{
            topsort(myMap); -- performs topological sort
            printList.print_new_line(); -- prints the tasks in the correct order
        }fi;
    }};
};
