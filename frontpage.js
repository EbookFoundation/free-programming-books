import React, { Component, PropTypes } from 'react'
import useSheet from 'react-jss'

class Frontpage extends Component {
  static propTypes = {
    sheet: PropTypes.object.isRequired,
  }

  render() {
    const { classes } = this.props.sheet

    return (
      <div className={classes.greeting}>Hello world!</div>
    )
  }
}

const styles = {
  greeting: {
    color: 'pink',
  },
}

export default useSheet(styles)(Frontpage)