
use smallvec::SmallVec;

#[derive(Debug)]
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    fn area(&self) -> u32 {
        self.width * self.height
    }

    fn can_hold(&self, other: &Rectangle) -> bool {
        self.width > other.width && self.height > other.height
    }

    fn square(size: u32) -> Self {
        Self {
            width: size,
            height: size,
        }
    }
}

fn main() {
    println!("Hello, world!");

    // var
    let mut x = 5;
    println!("The value of x is: {x}");
    x = 6;
    println!("The value of x is: {x}");

    // constant
    const THREE_HOURS_IN_SECONDS: u32 = 60 * 60 * 3;


    let rect1 = Rectangle {
        width: 30,
        height: 50,
    };

    println!(
        "The area of the rectangle is {} square pixels.",
        rect1.area()
    );

    // vector
    let mut vec = Vec::new();
    vec.push(1);
    vec.push(2);
    vec.push(3);

    println!("{:?}", vec);

    // small vec
    let mut small_vec: SmallVec<[i32; 4]> = SmallVec::new();
    small_vec.push(1);
    small_vec.push(2);
    small_vec.push(3);

    println!("{:?}", small_vec);
}
