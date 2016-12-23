#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lanedetection import LaneModel
import rospy
import cv2
from sensor_msgs.msg import Image
from std_msgs.msg import Float64
from cv_bridge import CvBridge, CvBridgeError

NODE_NAME = "lane_tracking"
SUB_TOPIC = "image"
PUB_TOPIC = "debug_image"
PUB_SETPOINT_TOPIC = "setpoint"
PUB_STATE_TOPIC = "state"
QUEUE_SIZE = 1
# valide default Werte für eine Bildauflösung von 320x240
DEFAULT_LANE_WIDTH = 20
DEFAULT_SEGMENT_START = 210
DEFAULT_SEGMENT_AMOUNT = 1


class LaneTrackingNode:

    def __init__(self, node_name, sub_topic, pub_topic, pub_setpoint_topic, pub_state_topic):
        self.bridge = CvBridge()
        lane_width = rospy.get_param("/autonomous_driving/lane_tracking_node/lane_width", DEFAULT_LANE_WIDTH)
        segment_start = rospy.get_param("/autonomous_driving/lane_tracking_node/segment_start", DEFAULT_SEGMENT_START)
        segment_amount = rospy.get_param("/autonomous_driving/lane_tracking_node/segment_amount", DEFAULT_SEGMENT_AMOUNT)
        self.lane_model = LaneModel(lane_width, segment_amount, segment_start)
        self.image_pub = rospy.Publisher(pub_topic, Image, queue_size=QUEUE_SIZE)
        self.setpoint_pub = rospy.Publisher(pub_setpoint_topic, Float64, queue_size=QUEUE_SIZE)
        self.state_pub = rospy.Publisher(pub_state_topic, Float64, queue_size=QUEUE_SIZE)

        rospy.init_node(node_name, anonymous=True)

        self.image_sub = rospy.Subscriber(sub_topic, Image, self.callback)

        rospy.spin()

    def callback(self, data):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
            heigth, width, _ = cv_image.shape
        except CvBridgeError as e:
            rospy.logerr(e)

        self.lane_model.update_segments(cv_image.copy())
        self.lane_model.draw_segments(cv_image)
        state_point_x = self.lane_model.state_point_x()

        try:
            self.image_pub.publish(self.bridge.cv2_to_imgmsg(cv_image, "bgr8"))
            self.setpoint_pub.publish(0.0)
            if state_point_x:
                self.state_pub.publish(state_point_x - int(width/2))
        except CvBridgeError as e:
            rospy.logerr(e)


def main():
    try:
        LaneTrackingNode(NODE_NAME, SUB_TOPIC, PUB_TOPIC, PUB_SETPOINT_TOPIC, PUB_STATE_TOPIC)
    except KeyboardInterrupt:
        rospy.loginfo("Shutting down node %s", NODE_NAME)

if __name__ == '__main__':
    main()
