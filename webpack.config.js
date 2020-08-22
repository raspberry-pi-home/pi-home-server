const {name: libraryName} = require('./package.json');
const WebpackShellPlugin = require('webpack-shell-plugin');

const outputFile = (mode) => mode === 'production' ? `${libraryName}.min.js` : `${libraryName}.js`;
const plugins = () => {
  if (process.env.NODE_ENV === 'development') {
    return [
      new WebpackShellPlugin({
        onBuildEnd: ['npm run start:dev']
      })
    ];
  }
}

module.exports = (env, argv) => ({
  entry: `${__dirname}/src/index`,
  target: 'node',
  output: {
    path: `${__dirname}/lib`,
    filename: outputFile(argv.mode),
    library: libraryName,
    libraryTarget: 'umd',
    umdNamedDefine: true,
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.json']
  },
  module: {
    rules: [{
      // Include ts, tsx, js, and jsx files.
      test: /\.(ts|js)x?$/,
      exclude: /node_modules/,
      loader: 'babel-loader'
    }]
  },
  plugins: plugins(),
  externals: {
    epoll: {
      commonjs: 'epoll',
      commonjs2: 'epoll',
      amd: 'epoll'
    }
  }
});
