class Main inherits IO {
    main() : Object {
        {
            out_string("Calling abort...\n");
            abort();  -- Calls the `abort` method from the `Object` class
        }
    };
};