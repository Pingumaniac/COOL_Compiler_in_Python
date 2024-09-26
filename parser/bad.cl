-- Uncomment each portion for testing


-- invalid class syntax


-- class Main AlsoMain{

-- };



-- class Main {

-- }



-- class class Main {

-- };



-- class Main inherits{

-- };



-- class Main inherits A B{

-- };



-- class Main inherits A inherits B{

-- };



-- class Main inherits A inherits class{

-- };



-- class Main inherits IO{
--     class Main2 inherits IO{

--     };
--};



-- class Main inherits IO{
    
-- }
-- class Main2{

-- };


-- invalid features
-- invlaid private variables


-- class Main inherits IO{
-- Int a;
-- };


-- class Main inherits IO{
-- Int : a;
--};


-- class Main inherits IO{
-- a Int;
-- };


-- class Main inherits IO{
-- a : Int String;
-- };


-- class Main inherits IO{
-- a : Int <- Int;
-- };


-- class Main inherits IO{
-- a b: Int;
-- };


-- class Main inherits IO{
-- a : Int <- 5 Int;
-- };


-- class Main inherits IO{
-- a : Int <- 5 <-4;
-- };


-- invalid operators


-- class Main inherits IO{
-- a : Int <- 5 +;
-- };
 

-- class Main inherits IO{
-- a : Int <- 5 + 5 5;
-- };


-- class Main inherits IO{
-- a : Int <- + 5 + 5 + 5;
-- };


-- invalid methods


-- class Main inherits IO{
--     reverseInsert Int( news: String): List{
--         if isNil() then
--             (new ListNode).init(news, self)
--         else{
--             next <- next.reverseInsert(news);
--             self;
--         } fi
--     };
-- };


-- class Main inherits IO{
--     reverseInsert ( news: String Int): List{
--         if isNil() then
--             (new ListNode).init(news, self)
--         else{
--             next <- next.reverseInsert(news);
--             self;
--         } fi
--     };
-- };


-- class Main inherits IO{
--     reverseInsert ( news: String, Int): List{
--         if isNil() then
--             (new ListNode).init(news, self)
--         else{
--             next <- next.reverseInsert(news);
--             self;
--         } fi
--     };
-- };


-- class Main inherits IO{
--     reverseInsert ( news: String, Int): {
--         if isNil() then
--             (new ListNode).init(news, self)
--         else{
--             next <- next.reverseInsert(news);
--             self;
--         } fi
--     };
-- };


-- class Main inherits IO{
--     reverseInsert ( news: String, Int): List{
--         if isNil() then
--             (new ListNode).init(news, self)
--         else{
--             next <- next.reverseInsert(news);
--             self;
--         } fi
--     }
-- };


-- class Main inherits IO{
--     reverseInsert : Int( news: String, Int): List{
--         if isNil() then
--             (new ListNode).init(news, self)
--         else{
--             next <- next.reverseInsert(news);
--             self;
--         } fi
--     };
-- };


-- class Main inherits IO{
--     reverseInsert : Int( news: String, Int): List{
--         if isNil() then
--             (new ListNode).init(news, self)
--         else{
--             next <- next.reverseInsert(news);
--             self;
--         } fi
--     };}
-- };


-- incorrect loop



-- class Main inherits IO{
--     reverseInsert : Int( news: String, Int): List{
--         if isNil() then
--             (new ListNode).init(news, self)
--         else{
--             next <- next.reverseInsert(news);
--             self;
--         } 
--     };
-- };



-- class Main inherits IO{
--     reverseInsert : Int( news: String, Int): List{
--         if isNil() then
--             (new ListNode).init(news, self)
--    
--     };
-- };


-- other errors


-- class Main inherits IO{
--     reverseInsert : Int( news: String, Int): List{
--         if isNil() then
--             (new ListNode)init(news, self)
--         else{
--             next <- next.reverseInsert(news);
--             self;
--         } fi
--     };
-- };


-- class Main inherits IO{
--     reverseInsert : Int( news: String, Int): List{
--         if isNil() then
--             (new ListNode)init(news, self)
--         else{
--             next <- next.reverseInsert(news)
--             self
--         } fi
--     };
-- };


-- class Main inherits IO{
--     reverseInsert : Int( news: String, Int): List{
--         if isNil() then
--             (new ListNode).init(news, self);
--         else{
--             next <- next.reverseInsert(news);
--             self;
--         } fi
--     };
-- };


-- class Main inherits IO{
--     reverseInsert : Int( news: String, Int): List{
--         if isNil() then
--             (new ListNode)init(news, self)
--         else{
--             next <- next.reverseInsert(news);
--             self;
--             Int;
--         } fi
--     };
-- };