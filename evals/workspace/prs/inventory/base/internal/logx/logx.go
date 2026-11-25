// Package logx is a thin wrapper over the standard logger.
package logx

import "log"

func Infof(format string, args ...any)  { log.Printf("INFO "+format, args...) }
func Errorf(format string, args ...any) { log.Printf("ERROR "+format, args...) }
