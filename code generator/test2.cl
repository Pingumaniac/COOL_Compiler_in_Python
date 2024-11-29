-- Main class for the program
class Main {
    counter : Int; -- Integer variable to act as a counter

    -- Main method of the program
    main() : Object {
      -- Create a new instance of IO to perform output operations
      (new IO).out_string(
        while (counter < 10) -- Loop while the counter is less than 10
          loop
            counter <- counter + 1 -- Increment the counter by 1
          pool.type_name() -- Get the type of the result of the while-loop (always "Object" in COOL)
      );
    };
  };
