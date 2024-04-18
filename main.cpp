#include <iostream>
#include <opencv2/opencv.hpp>

int main(){
    cv::VideoCapture source("https://youtu.be/dQw4w9WgXcQ");
    std::cout << source.isOpened() << std::endl;
    source.~VideoCapture();
}