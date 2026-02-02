use std::cell::RefCell;
use std::rc::Rc;


// 定义节点结构体
struct Node<T> {
    data: T,
    prev: Option<Rc<RefCell<Node<T>>>>,  // 使用 Option 和 Rc 包裹前一个节点
    next: Option<Rc<RefCell<Node<T>>>>,  // 使用 Option 和 Rc 包裹下一个节点
}

impl<T> Node<T> {
    // 创建一个新的节点
    fn new(data: T) -> Rc<RefCell<Self>> {
        Rc::new(RefCell::new(Node {
            data,
            prev: None,
            next: None,
        }))
    }
}

// 定义双向链表
struct LinkedList<T> {
    head: Option<Rc<RefCell<Node<T>>>>,  // 链表头节点
    tail: Option<Rc<RefCell<Node<T>>>>,  // 链表尾节点
}

impl<T: std::fmt::Display> LinkedList<T> {
    // 创建一个新的空链表
    fn new() -> Self {
        LinkedList { head: None, tail: None }
    }

    // 向链表尾部添加一个新的节点
    fn append(&mut self, data: T) {
        let new_node = Node::new(data);

        match self.tail.take() {
            Some(old_tail) => {
                // 将旧尾节点的 next 指向新节点
                old_tail.borrow_mut().next = Some(new_node.clone());
                // 将新节点的 prev 指向旧尾节点
                new_node.borrow_mut().prev = Some(old_tail);
                // 更新链表的尾节点
                self.tail = Some(new_node);
            }
            None => {
                // 如果链表为空，新的节点即为头节点和尾节点
                self.head = Some(new_node.clone());
                self.tail = Some(new_node);
            }
        }
    }

    // 打印链表中的所有节点
    fn print_list(&self) {
        let mut current = self.head.clone();
        while let Some(node) = current {
            print!("{} ", node.borrow().data);
            current = node.borrow().next.clone();
        }
        println!();
    }

    // 从链表中移除尾部的节点
    fn remove_tail(&mut self) {
        if let Some(tail) = self.tail.take() {
            let prev_node = tail.borrow_mut().prev.take();
            if let Some(prev) = prev_node {
                // 将新尾节点的 next 置为 None
                prev.borrow_mut().next = None;
                // 更新链表的尾节点
                self.tail = Some(prev);
            } else {
                // 如果没有前驱节点，说明链表为空
                self.head = None;
                self.tail = None;
            }
        }
    }
}



fn main() {
    println!("Hello, world!");
    let mut list = LinkedList::new();
    
    // 向链表中添加节点
    list.append(10);
    list.append(20);
    list.append(30);
    
    // 打印链表
    list.print_list();  // 输出: 10 20 30
}
