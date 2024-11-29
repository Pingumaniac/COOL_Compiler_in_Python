-- Define a class that inherits from IO for input/output operations
class LifeSimulation inherits IO {
    grid_state : String; -- Stores the current state of the cell grid as a string

    -- Constructor to initialize the grid state
    init(initial_grid : String) : SELF_TYPE {
        {
            grid_state <- initial_grid; -- Assign the initial grid state
            self; -- Return the current object
        }
    };

    -- Method to print the current grid state
    display_grid() : SELF_TYPE {
        {
            out_string(grid_state.concat("\n")); -- Print the grid state followed by a newline
            self; -- Return the current object
        }
    };

    -- Method to calculate the number of cells in the grid
    total_cells() : Int {
        grid_state.length() -- Return the length of the grid state string
    };

    -- Method to get the value of a cell at a specific position
    get_cell(index : Int) : String {
        grid_state.substr(index, 1) -- Return the substring at the specified position
    };

    -- Method to get the left neighbor of a cell
    left_neighbor(index : Int) : String {
        if index = 0 then
            get_cell(total_cells() - 1) -- Wrap around to the last cell if at the beginning
        else
            get_cell(index - 1) -- Otherwise, return the previous cell
        fi
    };

    -- Method to get the right neighbor of a cell
    right_neighbor(index : Int) : String {
        if index = total_cells() - 1 then
            get_cell(0) -- Wrap around to the first cell if at the end
        else
            get_cell(index + 1) -- Otherwise, return the next cell
        fi
    };

    -- Method to determine the next state of a cell based on its neighbors
    next_cell_state(index : Int) : String {
        if (if get_cell(index) = "X" then 1 else 0 fi
            + if left_neighbor(index) = "X" then 1 else 0 fi
            + if right_neighbor(index) = "X" then 1 else 0 fi
            = 1)
        then
            "X" -- Cell survives if exactly one of the three cells is alive
        else
            "." -- Otherwise, the cell dies
        fi
    };

    -- Method to evolve the entire grid to the next generation
    update_grid() : SELF_TYPE {
        (let index : Int in -- Initialize an index variable
        (let grid_size : Int <- total_cells() in -- Get the total number of cells
        (let new_state : String in -- Temporary string to store the new grid state
            {
                while index < grid_size loop -- Loop through all cells
                    {
                        new_state <- new_state.concat(next_cell_state(index)); -- Append the new state of the cell
                        index <- index + 1; -- Move to the next cell
                    }
                pool;
                grid_state <- new_state; -- Update the grid state with the new state
                self; -- Return the current object
            }
        ) ) )
    };
};

-- Main class to simulate the cellular automaton
class Main {
    automaton : LifeSimulation; -- Instance of the LifeSimulation class

    main() : SELF_TYPE {
        {
            automaton <- (new LifeSimulation).init("         X         "); -- Initialize with a starting state
            automaton.display_grid(); -- Print the initial state
            (let iterations : Int <- 20 in -- Set the number of generations to simulate
                while 0 < iterations loop -- Loop for the specified number of generations
                    {
                        automaton.update_grid(); -- Update the grid to the next generation
                        automaton.display_grid(); -- Print the new state
                        iterations <- iterations - 1; -- Decrease the iteration counter
                    }
                pool
            );
            self; -- Return the current object
        }
    };
};
