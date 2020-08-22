import os from 'os'
import fs from 'fs'
import http  from 'http'
import https from 'https'
import express from 'express'
import helmet from 'helmet'
import morgan from 'morgan'
import boxen from 'boxen'
import chalk from 'chalk'
import cors from 'cors'

const serverHandler = (httpMode: string, port: number) => {
  const interfaces = os.networkInterfaces()

  const getNetworkAddress = () => {
    for (const name of Object.keys(interfaces)) {
      // @ts-ignore TS2532
      for (const localInterface of interfaces[name]) {
        const { address, family, internal } = localInterface
        if (family === 'IPv4' && !internal) {
          return address
        }
      }
    }
  }

  const localAddress = `${httpMode}://localhost:${port}`
  const networkAddress = getNetworkAddress()

  let message = chalk.green('Server running!')

  const prefix = networkAddress ? '- ' : ''
  const space = networkAddress ? '            ' : '  '

  message += `\n\n${chalk.bold(`${prefix}Local:`)}${space}${localAddress}`

  if (networkAddress) {
    message += `\n${chalk.bold('- On Your Network:')}  ${httpMode}://${networkAddress}:${port}`
  }

  // eslint-disable-next-line no-console
  console.log(boxen(message, {
    padding: 1,
    borderColor: 'green',
    margin: 1,
  }))
}

export const server = () => {
  // app setup
  const app: express.Application = express()
  const port: number = process.env.PORT ? +process.env.PORT : 8000
  const httpMode: string = fs.existsSync('server.key') && fs.existsSync('server.cert') ? 'https' : 'http'

  app.use(helmet())
  app.use(cors())
  app.use(express.json())
  app.use(morgan('common'))

  // routes setup
  app.get('/', (req, res) => {
    res.send('Welcome to raspberry-pi-server!')
  })

  app.use((err: any, req: any, res: any, next: any) => {
    if (process.env.DEBUG) {
      // eslint-disable-next-line no-console
      console.error(err.stack)
    }
    res.status(500).send(err.message)
  })

  // server bootstraping
  let server
  if (httpMode === 'https') {
    server = https.createServer({
      key: fs.readFileSync('server.key'),
      cert: fs.readFileSync('server.cert'),
    }, app)
  } else {
    server = http.createServer({}, app)
  }

  server.listen(port, () => serverHandler(httpMode, port))
}
