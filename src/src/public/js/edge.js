//Edge model as connection between 2 Node instances
export class Edge{
    constructor(node1,node2){
        this.node1 = node1;
        this.node2 = node2;
    }

    //Returns the start anchor of the edge, which is the center of the first node (position of the line connection point)
    getStartAnchor(){
        return this.node1.center;
    }
    //Returns the start anchor of the edge, which is the center of the second node (position of the line connection point)
    getEndAnchor(){
        return this.node2.center;
    }
}