import { Point } from "./point.js";
//Class for storing node centers and cluster indices
export class Node{
    constructor(index,x,y){
        this.index = index;
        this.center = new Point(x,y);
    }
}