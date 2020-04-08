import React from "react";
import Avatar from "./Avatar";

// Receives just a name? Score? A little pre-gen Avatar? A colour?

export default class Player extends React.Component {
  render() {
    return (
      <>
        <div style={{ marginTop: 10, marginBottom: 10, display: "flex" }}>
          <div style={{ width: 50, padding: 0 }}>
            <Avatar avatarNum={this.props.avatarNum} name={this.props.name} />
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "start",
              marginLeft: "10px",
            }}
          >
            <div>{this.props.name}</div>
            <div className={"light"}>
              {this.props.score} point{this.props.score === 1 ? false : "s"}{" "}
              total
            </div>
          </div>
        </div>
        <div style={{ height: 0, border: "1px solid #EDEDED" }} />
      </>
    );
  }
}
