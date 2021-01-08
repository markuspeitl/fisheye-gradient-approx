import { Point } from "./point.js";

/*A lens class that distorts the points passed to it by
fisheye lens distortion*/
export class Lens{

    constructor(center,radius){
        this.center = center;
        this.radius = radius;
        Lens.m = 4;
        Lens.origMixFactor = 1.0;

        this.useDistortionSphere = false;
    }

    //Set a difference focalCenter of the lens
    setCenter(center){
        this.center = center;
    }
    //Set a different focal radius of the lens
    setRadius(radius){
        this.radius = radius;
    }

    //Calculate the euclidian distance between 2 points
    calcDistance(point1,point2){
        return Math.sqrt(Math.pow(point2.x - point1.x,2) + Math.pow(point2.y - point1.y,2));
    }
    //Calculate the length of a vector
    calcLength(vector){
        return Math.sqrt(Math.pow(vector.x,2) + Math.pow(vector.y,2));
    }

    //Linear distortion scaling for increasing point size towards the center and decreasing point size towards the boundary
    //Returns the scaled point size
    getDistortedScale(point,refpos){
        if(!refpos){
            return point;
        }

        //Calculate distance to given reference point (node position)
        var distancePoint = this.calcDistance(refpos,this.center);

        //Linear distortion inside boundary
        var scaleFactor = 0.3;
        if(distancePoint < this.radius){
            scaleFactor = (400 - distancePoint)/400
        }
        //Constant size outside boundary
        if(scaleFactor < 0.4){
            scaleFactor = 0.4;
        }

        scaleFactor = scaleFactor * 2.5;

        //Scale passed point by scaleFactor and return
        return new Point(point.x * scaleFactor, point.y * scaleFactor);
    }

    //Fisheye distortion of the point position
    //Returns point position distorted by the fisheye lens
    getDistortedPoint(point){

        //Distance between node position and focal center
        var distancePoint = this.calcDistance(point,this.center);
        
        //Normalized direction from focal center to node position
        var direction = new Point((point.x - this.center.x)/distancePoint,(point.y - this.center.y)/distancePoint);

        //Projected point of boundary space (slide alongside direction to intersection with focal boundary)
        var boundaryDiff = new Point(direction.x * this.radius, direction.y * this.radius);

        //Distance between Boundary point and focal point
        var distanceBoundary = this.calcLength(boundaryDiff);

        //Ratio of nodedistance to focal point/ boundarydistance to focal point
        var betha = distancePoint/distanceBoundary;

        if(this.useDistortionSphere && distancePoint > distanceBoundary){
            betha = distanceBoundary/distancePoint;
        }

        //Nonlinear distortion of distance ratio
        var bethadist = ((Lens.m+1)*betha)/(Lens.m*betha + 1);

        if(!this.useDistortionSphere && distancePoint > distanceBoundary){
            //Interpolate with original layout positions, if outside boundary
            bethadist = (1-Lens.origMixFactor) * bethadist + Lens.origMixFactor * (distancePoint/distanceBoundary)
        }

        //Calculate final distorted point with Nonlinear distortion factor
        var distortedPoint = new Point(this.center.x + boundaryDiff.x * bethadist,this.center.y + boundaryDiff.y * bethadist);

        return distortedPoint;
    }
}