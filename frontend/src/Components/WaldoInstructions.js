import React from "react";
import Container from "react-bootstrap/Container";
import Carousel from "react-bootstrap/Carousel";

import matzahInstruction1 from "../Images/Instructions/matzah1Mobile.png";
import matzahInstruction2 from "../Images/Instructions/matzah2Mobile.png";

export default class WaldoInstructions extends React.Component {
  render() {
    return (
      <div>
        <Carousel controls={false}>
          <Carousel.Item>
            <div
              style={{
                position: "absolute",
                backgroundColor: "white",
                opacity: 0.8,
                height: 90,
                width: "100%",
                zIndex: 500,
              }}
            />
            <div
              style={{
                position: "absolute",
                left: "10%",
                width: "80%",
                top: "20px",
                height: "52px",
                background: "#FFFFFF",
                boxShadow: "0px 1px 7px rgba(0, 0, 0, 0.13)",
                borderRadius: "10px",
                zIndex: 501,
                opacity: 1,
                fontSize: "14px",
                padding: "5px",
              }}
            >
              Zoom in on a location and try to find the afikoman hidden in the
              scene.
            </div>
            <img src={matzahInstruction1} alt="Example Find the Matzah 1" />
          </Carousel.Item>
          <Carousel.Item>
            <div
              style={{
                position: "absolute",
                backgroundColor: "white",
                opacity: 0.8,
                height: 90,
                width: "100%",
                zIndex: 500,
              }}
            />
            <div
              style={{
                position: "absolute",
                left: "10%",
                width: "80%",
                top: "20px",
                height: "52px",
                background: "#FFFFFF",
                boxShadow: "0px 1px 7px rgba(0, 0, 0, 0.13)",
                borderRadius: "10px",
                zIndex: 501,
                opacity: 1,
                fontSize: "14px",
                padding: "5px",
              }}
            >
              When you find it, tap it to win the game!
            </div>
            <img src={matzahInstruction2} alt="Example Find the Matzah 2" />
          </Carousel.Item>
        </Carousel>
      </div>
    );
  }
}