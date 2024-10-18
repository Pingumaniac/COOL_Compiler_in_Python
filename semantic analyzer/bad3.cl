class Main inherits Object{
    a: Int;
    b: Int <- 2 + "a";
    c: Int <- 3;
    add(a: Int, b: Int): Int{
        a + b
    };

    main(): Object{
        self
    };

    
};

class ClassA{
    a: Int <- 1+1;
    init(): String{
        "not an int"
    };
};

class ClassB inherits ClassA{
    b: Int;
};