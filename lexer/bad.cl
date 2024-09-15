class Main inherits IO {
    a: Int;
    b: String;
    c: Int <- a + b;  -- Invalid addition of Int and String (lexer should work but parser will fail)
    (* 
    normal multiline comment
    *)
    d: Int -- missing semicolon, error for the parser but lexer should not report error
    (*
    (* 
    normal nested multiline comment
    *)
    *)

    -- lone underscore
    _

    -- integer too large
    12345678901234567890

    -- string that's too long
    "qbdgqwiudciuqfhniqvwhfiowhnfuiwhfuireguibwvbhfociuwhiofucguhbfiuwevniuowqnvguwigfcniojncokwmqfnojiwqbhfbuivbhwocjjxfoifnibgubwhvqufwioejnciwirhgbuivwfgbuiwehfciofniowhbfvowhbfiocwnjofnjcof"


    invalidtype : String <- 10;  -- Invalid variable type (lexer should work but parser will fail)


    (* (* unclosed multiline comment, the lexer should report error *)

    - incorrect single line comment, lexer should think its a minus sign and produce no error but parser should produce an error

    foo(x: Int, y: Int): Object {
        if y > x then -- Lexer should report error for illegal character ">"
            out_string("x is smaller than y\n"); -- Invalid semicolon (lexer should work but parser will fail)
        else
            out_string("x is greater than or equal to y\n"); -- Invalid semicolon (lexer should work but parser will fail)
        fi;
        x + y;
    };

    main() : Object {
        {
            out_string("Vanderbilt); -- Unclosed string, lexer should report error
            a <- a + b;  -- Invalid addition of Int and String (lexer should work but parser will fail)
        }
    };
    
  };