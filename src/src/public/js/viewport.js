import { Point } from "./point.js"
import { Rect } from "./rect.js"

//Class which transforms data positions/scales to view positions/scales
//defining the data viewport rectangles
export class ViewPort{

    constructor(){
        //Reference data display window
        this.dataRect = new Rect(-100,-100,1100,1100)
        //Reference screen size
        this.screenRect = new Rect(0,0,1920,1080);
        this.lens = null;
    }

    //Apply lens to position transformation chain
    applyLens(lens){
        this.lens = lens;
    }
    //Remove lens from position transformation chain
    removeLens(){
        this.lens = null;
    }

    //Data Position to screen coordinates Transformation
    //In: dataPoint OUT: screenPoint
    dataPointToScreenPoint(point){
        var screenPoint = new Point(0,0);

        //Lens distortion of point
        if(this.lens){
            point = this.lens.getDistortedPoint(point)
        }

        //Rectangular space transformation
        var xPercent = (point.x-this.dataRect.x)/this.dataRect.w;
        var yPercent = (point.y-this.dataRect.y)/this.dataRect.h;
        screenPoint.x = this.screenRect.x + this.screenRect.w * xPercent;
        screenPoint.y = this.screenRect.y + this.screenRect.h * yPercent;
        return screenPoint;
    }
    //Data size to screen scales Transformation
    //In: dataSize OUT: screenSize
    scaleDataPointToScreenPoint(point,refpos){

        //Lens distortion of scale
        if(this.lens){
            point = this.lens.getDistortedScale(point,refpos)
        }

        //Rectangular space transformation
        var screenPoint = new Point(0,0);
        var xPercent = (point.x)/this.dataRect.w;
        var yPercent = (point.y)/this.dataRect.h;
        screenPoint.x = this.screenRect.w * xPercent;
        screenPoint.y = this.screenRect.h * yPercent;
        return screenPoint;
    }

    //Screen coordinates to data positions transformation
    //In: screenPoint OUT: dataPoint 
    screenPointToDataPoint(point){
        var dataPoint = new Point(0,0);
        var xPercent = (point.x - this.screenRect.x)/this.screenRect.w;
        var yPercent = (point.y - this.screenRect.y)/this.screenRect.h;
        dataPoint.x = this.dataRect.x + this.dataRect.w * xPercent;
        dataPoint.y = this.dataRect.y + this.dataRect.h * yPercent;
        return dataPoint;
    }
    //Screen size to data size transformation
    //In: screenSize OUT: dataSize
    scaleScreenPointToDataPoint(point){
        var dataPoint = new Point(0,0);
        var xPercent = (point.x)/this.screenRect.w;
        var yPercent = (point.y)/this.screenRect.h;
        dataPoint.x = this.dataRect.w * xPercent;
        dataPoint.y = this.dataRect.h * yPercent;
        return dataPoint;
    }

    //Helpers

    //Shift data viewport by screenShift, can be used for panning
    moveScreen(screenShift){
        var dataShift = this.scaleScreenPointToDataPoint(screenShift);
        this.dataRect.x += dataShift.x;
        this.dataRect.y += dataShift.y;
    }
    //Set different screen width and height (update screen rect when resizing)
    resizeScreenRect(sizex,sizey){
        this.screenRect.w = sizex;
        this.screenRect.h = sizey;
    }


}