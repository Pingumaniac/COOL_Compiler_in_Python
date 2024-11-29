-- Base class for demonstration, inherits IO for input/output operations
class RootClass inherits IO
{
  -- Method to identify and print the type of the given object
  identify_object( entity : Object ) : Object
  {
    {
      out_string( entity.type_name() ); -- Print the type name of the object
      out_string( "\n" ); -- Print a newline for formatting
    }
  };

  -- Test method to demonstrate object identification and polymorphism
  demo_behavior() : Object
  {
    {
      identify_object( new RootClass ); -- Identify an object of RootClass
      identify_object( new SubClass ); -- Identify an object of SubClass

      -- Demonstrate polymorphism with a let expression
      let poly_instance : RootClass <- new SubClass in
        identify_object( poly_instance ); -- Identify the type of the polymorphic instance

      identify_object( self ); -- Identify the type of the current object
    }
  };
};

-- Subclass inheriting from RootClass
class SubClass inherits RootClass
{
};

-- Main class serving as the entry point of the program
class Main
{
  -- Main method to execute the test behavior
  main() : Object
  {
    (new SubClass).demo_behavior() -- Create a SubClass instance and call the demo_behavior method
  };
};
